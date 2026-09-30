"""Kesintide sonuçları koruyan ve farklı deneyleri karıştırmayan değerlendirme."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         suffix=".tmp", delete=False) as stream:
            name = stream.name
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def evaluate(cases, configuration, output, ask, resume=False):
    if not cases or any(not isinstance(c, dict) or not c.get("question", "").strip() for c in cases):
        raise ValueError("Değerlendirme soruları boş olamaz.")
    path = Path(output)
    identity = digest({"cases": cases, "configuration": configuration})
    run = {"schema_version": 1, "run_identity": identity,
           "started_at": datetime.now(timezone.utc).isoformat(),
           "configuration": configuration, "total_cases": len(cases), "results": []}
    if path.exists():
        if not resume:
            raise ValueError("Sonuç dosyası zaten var; --resume veya farklı --output kullanın.")
        run = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(run, dict) or run.get("run_identity") != identity:
            raise ValueError("Soru, model, kod veya indeks değişmiş; farklı --output kullanın.")
    elif resume:
        raise ValueError("Devam edilecek sonuç dosyası bulunamadı.")
    # Write before the first inference so even a first-question failure leaves provenance.
    save_json(path, run)
    for index in range(len(run["results"]), len(cases)):
        case = cases[index]
        print(f"[{index + 1}/{len(cases)}] {case['question']}", flush=True)
        # Failure/KeyboardInterrupt propagates. Resume retries the unfinished question.
        result = ask(case["question"])
        result["expected"] = case
        result["retrieval_hit"] = (any(h["chunk"]["source"] == case["source"]
                                       for h in result["retrieved"]) if case.get("source") else None)
        result["human_review"] = "pending"
        run["results"].append(result)
        save_json(path, run)
        print(f"  {result['status']} | {result['total_seconds']:.2f} saniye", flush=True)
    return run


def summarize(run):
    legacy = isinstance(run, list)
    results = run if legacy else run["results"]
    answerable = [r for r in results if r.get("expected", {}).get("source")]
    outside = [r for r in results if r.get("expected", {}).get("expected_answer") == "abstain"]
    return {"completed_cases": len(results), "total_cases": None if legacy else run["total_cases"],
            "statuses": dict(Counter(r["status"] for r in results)),
            "retrieval_hits": sum(r.get("retrieval_hit") is True for r in answerable),
            "answerable_cases_evaluated": len(answerable),
            "out_of_scope_cases_evaluated": len(outside),
            "out_of_scope_abstentions": sum(r["status"] in {"no_context", "model_abstained"} for r in outside),
            "mean_seconds": round(sum(r["total_seconds"] for r in results) / len(results), 3) if results else None,
            "quality_note": "answered: generative modunda kaynak etiketi, extractive modunda kaynak cümlesi kimliği kontrol edilir. Soruyla ilgililik ve cevap yeterliliği insan incelemesi gerektirir; doğruluk onayı değildir."}
