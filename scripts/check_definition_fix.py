"""Kayıtlı çıktılarla sınırlı regresyon; yeni embedding veya LLM üretimi yapmaz."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ragapp.core import Chunk, Hit, answer
from ragapp.evidence import evidence_units, scope_definition
from ragapp.retrieval import rank_candidates

def replay(row):
    hits = [Hit(Chunk(**h["chunk"]), h["score"]) for h in row["retrieved"]]
    store = SimpleNamespace(retrieve=lambda *a, **k: hits)
    gen = SimpleNamespace(generate=lambda *a: row["model_output"])
    return answer(row["question"], store, None, gen, answer_mode="extractive")

def check():
    source = ROOT / "docs/evidence/notlarim-sohbet-first.json"
    original = json.loads(source.read_text(encoding="utf-8"))[0]
    result = replay(original)
    assert result["answer"] == "print yalnızca ekrana yazar; yazdırdığı değeri çağırana sonuç olarak vermez. [S2]"
    assert result["evidence_scope"]["excluded_ids"] == ["S1.13", "S1.14"]
    candidates = [(Chunk(**h["chunk"]), h["score"]) for h in original["retrieved"]]
    ranked = rank_candidates(original["question"], candidates, .35, "hybrid")
    assert ranked[0][0].source != "02-kosullar.txt"
    units, subject = scope_definition(original["question"], evidence_units([Hit(*x) for x in ranked]))
    assert units and all("print" in x["text"] for x in units.values())
    baseline = json.loads((ROOT / "docs/evidence/windows-cuda-quality-v3.json").read_text(encoding="utf-8"))
    previous = [replay(row) for row in baseline["results"]]
    unchanged = sum(new["answer"] == old["answer"] for old,new in zip(baseline["results"], previous) if old["status"] == "answered")
    assert unchanged == 17
    report = {
        "validation_type": "saved_candidates_and_output_replay",
        "new_model_inference": False,
        "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "definition_result_same_source_order": {k:result[k] for k in ("answer","status","evidence_scope","model_output")},
        "reranked_saved_candidates": [x[0].source for x in ranked],
        "offered_sentences_after_ranking": units,
        "previous_answerable_texts_unchanged": unchanged,
        "previous_out_of_scope_abstentions": sum(x["status"] in {"no_context","model_abstained"} for x in previous),
        "limitations": "Yeni sıralama yalnız kaydedilmiş üç adayla sınandı; tam indeks sorgusu veya yeni LLM yanıtı değildir. Önceki çıktılar eski kaynak kimlikleriyle tekrar işlendi. Windows model denemesi bekliyor."
    }
    return report

if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))

