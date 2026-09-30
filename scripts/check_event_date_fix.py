"""Kayıtlı kaynakları yeni tarih filtresinden geçirir; yeni model deneyi yapmaz."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ragapp.core import Chunk, Hit, answer

def replay(row):
    hits = [Hit(Chunk(**h["chunk"]), h["score"]) for h in row["retrieved"]]
    calls = []
    def generate(*args):
        calls.append(True)
        return row["model_output"]
    new = answer(row["question"], SimpleNamespace(retrieve=lambda *a, **k: hits), None,
                 SimpleNamespace(generate=generate), answer_mode="extractive")
    return {"question": row["question"], "old_status": row["status"], "status": new["status"],
            "old_answer": row["answer"], "answer": new["answer"],
            "answer_unchanged": row["answer"] == new["answer"],
            "scope": new["evidence_scope"], "replay_generator_called": bool(calls)}

def check():
    path = ROOT / "docs/evidence/pusula-first.json"
    raw = path.read_bytes()
    rows = json.loads(raw)
    results = [replay(row) for row in rows]
    assert len(results) == 6
    assert all(x["answer_unchanged"] for x in results[:5])
    assert results[5]["status"] == "no_context"
    assert results[5]["replay_generator_called"] is False
    previous = json.loads((ROOT / "docs/evidence/windows-cuda-quality-v3.json").read_text(encoding="utf-8"))["results"]
    old_results = [replay(row) for row in previous]
    assert sum(r["answer_unchanged"] for row,r in zip(previous,old_results) if row["status"]=="answered") == 17
    assert sum(r["status"] in {"no_context","model_abstained"} for r in old_results) == 7
    print_rows = json.loads((ROOT / "docs/evidence/print-after-definition-fix.json").read_text(encoding="utf-8"))
    print_results = [replay(row) for row in print_rows]
    assert all(r["answer_unchanged"] for r in print_results)
    return {"validation_type": "saved_context_and_output_replay", "new_model_inference": False,
            "input_sha256": hashlib.sha256(raw).hexdigest(), "pdf_cases": results,
            "previous_17_answers_unchanged": True, "previous_out_of_scope_abstentions": 7,
            "print_cases_unchanged": len(print_results),
            "limits": "Aynı kayıtlı kaynaklarla yeni kontrol çalıştırıldı. Yeni retrieval, LLM üretimi veya hız ölçümü değildir. Genel kapsam dışı soru başarımı ölçülmedi."}

if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))

