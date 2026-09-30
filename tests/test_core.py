"""Gerçek LLM kalitesini ölçmez; deterministik verilerle altyapıyı sınar."""
from pathlib import Path
import json
import math
import struct
import tempfile
from types import SimpleNamespace
import unittest
from ragapp.core import Store, split_text, cosine, normalized, answer, FALLBACK
from ragapp.foundry import tensor_vector


class FakeEmbedder:
    identity = "test-vectors-v1"

    def __init__(self):
        self.calls = 0

    def embed(self, texts):
        self.calls += len(texts)
        return [[1, 0] if "python" in text.lower() else [0, 1] for text in texts]

    def embed_query(self, text):
        return self.embed([text])[0]


class FakeGenerator:
    def __init__(self, output="Python açıklaması [S1]"):
        self.output, self.calls = output, 0

    def generate(self, system, user):
        self.calls += 1
        self.payload = user
        return self.output


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        (self.docs / "python.txt").write_text("Python ders notu", encoding="utf-8")
        self.store = Store(self.root / "db.sqlite")
        self.emb = FakeEmbedder()

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_chunking_coverage_and_overlap(self):
        self.assertEqual(split_text("a b c d e f g", 4, 1), ["a b c d", "d e f g"])
        self.assertEqual(split_text(""), [])
        with self.assertRaises(ValueError):
            split_text("a", 2, 2)

    def test_cosine_known_angles(self):
        self.assertAlmostEqual(cosine([3, 4], [6, 8]), 1)
        self.assertEqual(cosine([1, 0], [0, 2]), 0)
        self.assertEqual(cosine([1, 0], [-1, 0]), -1)
        for vector in ([0, 0], [], [math.nan], [math.inf]):
            with self.assertRaises(ValueError):
                normalized(vector)
        with self.assertRaises(ValueError):
            cosine([1], [1, 2])

    def test_ingest_idempotent_and_persistent(self):
        first = self.store.ingest(self.docs, self.emb)
        self.assertEqual(first["total_chunks"], 1)
        again = self.store.ingest(self.docs, self.emb)
        self.assertEqual(again["unchanged_documents"], 1)
        self.assertEqual(self.emb.calls, 1)
        with Store(self.root / "db.sqlite") as reopened:
            self.assertEqual(reopened.retrieve("Python", self.emb)[0].chunk.source, "python.txt")

    def test_changed_file_replaces_old_chunks(self):
        self.store.ingest(self.docs, self.emb)
        (self.docs / "python.txt").write_text("Python güncellenmiş not", encoding="utf-8")
        self.store.ingest(self.docs, self.emb)
        self.assertEqual(self.store.count(), 1)
        self.assertIn("güncellenmiş", self.store.retrieve("Python", self.emb)[0].chunk.content)

    def test_transaction_preserves_old_data_on_failure(self):
        self.store.ingest(self.docs, self.emb)
        (self.docs / "python.txt").write_text("Python yeni içerik", encoding="utf-8")
        (self.docs / "z.txt").write_text("", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.store.ingest(self.docs, self.emb)
        self.assertEqual(self.store.retrieve("Python", self.emb)[0].chunk.content, "Python ders notu")

    def test_changed_model_rejected(self):
        self.store.ingest(self.docs, self.emb)
        self.emb.identity = "other-model"
        with self.assertRaises(ValueError):
            self.store.retrieve("Python", self.emb)
        with self.assertRaises(ValueError):
            self.store.ingest(self.docs, self.emb)

    def test_bad_vector_batch_not_stored(self):
        self.emb.embed = lambda texts: []
        with self.assertRaises(ValueError):
            self.store.ingest(self.docs, self.emb)
        self.assertEqual(self.store.count(), 0)

    def test_blank_and_oversized_questions(self):
        for question in ("   ", "x" * 2001):
            with self.assertRaises(ValueError):
                self.store.retrieve(question, self.emb)

    def test_empty_database_does_not_call_model(self):
        gen = FakeGenerator()
        result = answer("Python", self.store, self.emb, gen)
        self.assertEqual(result["status"], "no_context")
        self.assertEqual(self.emb.calls, 0)
        self.assertEqual(gen.calls, 0)
        self.assertIsNone(result["generation_details"])

    def test_no_match_does_not_call_generator(self):
        self.store.ingest(self.docs, self.emb)
        gen = FakeGenerator()
        gen.last_timings = {"total_seconds": 999}  # Önceki sorunun süresi taşınmamalı.
        result = answer("Astronomi", self.store, self.emb, gen)
        self.assertEqual(result["answer"], FALLBACK)
        self.assertEqual(gen.calls, 0)
        self.assertIsNone(result["generation_details"])

    def test_answer_citations_resolve_to_retrieved_source(self):
        self.store.ingest(self.docs, self.emb)
        gen = FakeGenerator()
        result = answer("Python nedir?", self.store, self.emb, gen)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["citations"], [1])
        self.assertIn("[S1] python.txt (sayfa 1)", gen.payload)

    def test_invalid_citations_not_presented_as_answer(self):
        self.store.ingest(self.docs, self.emb)
        for output in ("Kaynak yok", "Yanıt [S99]", "Yanıt [S0]", "Yanıt [S1] [S999]"):
            result = answer("Python", self.store, self.emb, FakeGenerator(output))
            self.assertEqual(result["status"], "invalid_citations")

    def test_model_can_abstain_despite_retrieved_context(self):
        self.store.ingest(self.docs, self.emb)
        result = answer("Python", self.store, self.emb, FakeGenerator(FALLBACK))
        self.assertEqual(result["status"], "model_abstained")

    def test_citation_does_not_turn_refusal_into_an_answer(self):
        self.store.ingest(self.docs, self.emb)
        result = answer("Python", self.store, self.emb, FakeGenerator(FALLBACK + " [S1]"))
        self.assertEqual(result["status"], "model_abstained")
        self.assertEqual(result["citations"], [])

    def test_mixed_answer_and_refusal_is_not_accepted(self):
        self.store.ingest(self.docs, self.emb)
        result = answer("Python", self.store, self.emb, FakeGenerator("İddia. " + FALLBACK + " [S1]"))
        self.assertEqual(result["status"], "conflicting_answer")

    def test_comma_separated_refusal_is_not_a_conflicting_answer(self):
        self.store.ingest(self.docs, self.emb)
        result = answer("Python", self.store, self.emb, FakeGenerator(FALLBACK + " [S1], [S2]"))
        self.assertEqual(result["status"], "model_abstained")
        self.assertEqual(result["answer"], FALLBACK)
        self.assertEqual(result["citations"], [])

    def test_tensor_bytes_decoded_as_floats(self):
        tensor = SimpleNamespace(data_type=SimpleNamespace(name="FLOAT"), shape=[1, 2], data=struct.pack("=2f", 0.25, -0.5))
        self.assertEqual(tensor_vector(tensor), [0.25, -0.5])
        tensor.shape = [2, 2]
        with self.assertRaises(ValueError):
            tensor_vector(tensor)


if __name__ == "__main__":
    unittest.main()
