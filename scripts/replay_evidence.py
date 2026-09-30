"""Kayıtlı model çıktısını ayrıştırıcıyla tekrar işler; yeni LLM deneyi değildir."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ragapp.core import Chunk, Hit, answer
from ragapp.evaluation import digest, save_json


def replay(path):
    data = Path(path).read_bytes()
    run = json.loads(data)
    if run.get("configuration", {}).get("answer_mode") != "extractive":
        raise ValueError("Yalnız extractive deney kaydı desteklenir.")
    results = []
    for original in run["results"]:
        hits = [Hit(Chunk(**h["chunk"]), h["score"]) for h in original["retrieved"]]
        store = SimpleNamespace(retrieve=lambda *a, **kw: hits)
        generator = SimpleNamespace(generate=lambda *a: original["model_output"])
        result = answer(original["question"], store, None, generator, answer_mode="extractive")
        results.append({"question": original["question"],
                        "expected": original.get("expected", {}),
                        "original_status": original["status"], "status": result["status"],
                        "answer": result["answer"], "evidence": result["evidence"],
                        "answer_unchanged": result["answer"] == original["answer"]})
    outside = [r for r in results if r["expected"].get("expected_answer") == "abstain"]
    return {"validation_type": "recorded_output_replay", "input_sha256": hashlib.sha256(data).hexdigest(),
            "original_run_identity": run["run_identity"],
            "code_digest": digest({name: (ROOT/name).read_text(encoding="utf-8") for name in
                                    ("ragapp/core.py", "ragapp/evidence.py", "scripts/replay_evidence.py")}),
            "new_model_inference": False, "results": results,
            "summary": {"cases": len(results), "statuses": dict(Counter(r["status"] for r in results)),
                        "out_of_scope_abstentions": sum(r["status"] in {"no_context", "model_abstained"} for r in outside),
                        "out_of_scope_cases": len(outside),
                        "changed_statuses": sum(r["status"] != r["original_status"] for r in results)},
            "note": "Kayıtlı çıktılar tekrar ayrıştırıldı. Yeni üretim, hız veya genel kalite ölçümü değildir."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Çıktı dosyası zaten var; farklı yol kullanın.")
    result = replay(args.input)
    save_json(args.output, result)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
