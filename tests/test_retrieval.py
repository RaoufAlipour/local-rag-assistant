"""Gerçek arama hatasının küçük, model gerektirmeyen regresyonları."""
from pathlib import Path
import tempfile
import unittest

from ragapp.core import Chunk, Store, answer, FALLBACK, is_abstention
from ragapp.retrieval import lexical_scores, rank_candidates, tokenize


class RetrievalTests(unittest.TestCase):
    def test_one_exact_match_boosts_eligible_document_in_long_question(self):
        relevant = Chunk("api.txt", 1, 0, "flush tamponu boşaltır.")
        unrelated = Chunk("calendar.txt", 1, 0, "Takvim tarihini kontrol edin.")
        ranked = rank_candidates("flush ne işe yarar", [(unrelated, .38), (relevant, .36)], .35, "hybrid")
        self.assertEqual(ranked[0][0], relevant)
        # Aynı tek eşleşme, eşik altındaki belgeyi uzun soruda kurtarmaz.
        ranked = rank_candidates("flush ne işe yarar", [(unrelated, .38), (relevant, .1)], .35, "hybrid")
        self.assertEqual([x[0] for x in ranked], [unrelated])

    def test_exact_code_term_rescues_source_below_cosine_threshold(self):
        relevant = Chunk("options.txt", 1, 0, "The flag z enables compression.")
        other = Chunk("intro.txt", 1, 0, "An introduction to programs.")
        candidates = [(other, 0.6), (relevant, 0.2)]
        hybrid = rank_candidates("z", candidates, 0.35, "hybrid")
        semantic = rank_candidates("z", candidates, 0.35, "semantic")
        self.assertEqual(hybrid[0][0], relevant)
        self.assertEqual(hybrid[0][1], 0.2)  # Cosine puanı değiştirilmez.
        self.assertEqual(hybrid[0][4], ("z",))
        self.assertEqual([row[0] for row in semantic], [other])

    def test_query_without_matching_terms_does_not_rescue_weak_cosine(self):
        candidates = [(Chunk("note.txt", 1, 0, "Lists contain values."), 0.1)]
        self.assertEqual(rank_candidates("astronomy", candidates, 0.35, "hybrid"), [])

    def test_single_letter_terms_are_exact_and_case_normalized(self):
        scores = lexical_scores("W", ["while values", "Use w", "Use a"])
        self.assertEqual(scores[0][0], 0)
        self.assertGreater(scores[1][0], 0)
        self.assertEqual(scores[2][0], 0)
        self.assertIn("a", tokenize("a"))
        self.assertEqual(tokenize("İşlem"), tokenize("işlem"))

    def test_rare_term_outweighs_common_term(self):
        scores = lexical_scores("common unique", ["common unique", "common basic", "common other"])
        self.assertGreater(scores[0][0], scores[1][0])

    def test_one_incidental_word_in_long_query_does_not_rescue_context(self):
        candidate = Chunk("note.txt", 1, 0, "The previous value is replaced.")
        self.assertEqual(rank_candidates("previous astronomy discoveries", [(candidate, 0.1)], 0.35, "hybrid"), [])

    def test_hybrid_store_integration_uses_existing_vectors(self):
        class Embedder:
            identity = "retrieval-test"
            def embed(self, texts):
                return [[0, 1] for _ in texts]
            def embed_query(self, question):
                return [1, 0]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            docs = root / "docs"
            docs.mkdir()
            (docs / "note.txt").write_text("Option z enables compression.", encoding="utf-8")
            with Store(root / "index.db") as store:
                store.ingest(docs, Embedder())
                self.assertEqual(store.retrieve("z", Embedder(), mode="semantic"), [])
                hit = store.retrieve("z", Embedder(), top_k=1)[0]
                self.assertEqual(hit.chunk.source, "note.txt")
                self.assertEqual(hit.score, 0)
                self.assertEqual(hit.matched_terms, ("z",))


class AbstentionTests(unittest.TestCase):
    def test_citation_separators_in_refusal(self):
        for suffix in ("", " [S1]", " [S1] [S2]", " [S1], [S2]", " [S1]; [S2]", "\n[S1],\n[S2]"):
            with self.subTest(suffix=suffix):
                self.assertTrue(is_abstention(FALLBACK + suffix))

    def test_refusal_parser_keeps_additional_claims_visible(self):
        for text in ("İddia. " + FALLBACK, FALLBACK + " Ama yanıt 42. [S1]",
                     FALLBACK + " [S1], başka bilgi [S2]", FALLBACK + " ,", FALLBACK + " [Sx]"):
            with self.subTest(text=text):
                self.assertFalse(is_abstention(text))


if __name__ == "__main__":
    unittest.main()
