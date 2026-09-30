"""Alıntı bütünlüğü ve hatalı model çıktısında kapalı davranış; LLM kalite testi değildir."""
import json
from types import SimpleNamespace
import unittest
from ragapp.core import Chunk, Hit, answer, FALLBACK
from ragapp.evidence import evidence_units, parse_selection


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.hits = [Hit(Chunk("örnek.txt", 2, 0,
            'İlk değer 3.14 olur. print fonksiyonunun dönüş değeri None\'dır. '
            'return ValueError sınıfı döndürür.'), .6)]
        self.units = evidence_units(self.hits)

    def ask(self, raw, hits=None):
        generator = SimpleNamespace(generate=lambda *args: raw)
        store = SimpleNamespace(retrieve=lambda *args, **kwargs: self.hits if hits is None else hits)
        return answer("Dönüş değeri?", store, None, generator, answer_mode="extractive")

    def test_exact_text_and_source_order_preserved(self):
        result = self.ask('{"selections":["S1.3","S1.2"]}')
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["answer"], "print fonksiyonunun dönüş değeri None'dır. [S1]\nreturn ValueError sınıfı döndürür. [S1]")
        self.assertEqual(result["citations"], [1])
        self.assertEqual(result["evidence_validation"], "exact_source")
        for unit in result["evidence"]:
            self.assertIn(unit["text"], self.hits[0].chunk.content)

    def test_decimal_and_code_remain_unchanged(self):
        self.assertEqual(self.units["S1.1"]["text"], "İlk değer 3.14 olur.")

    def test_fabricated_or_malformed_selection_never_rendered(self):
        for raw in ('{"selections":["S99.1"]}', '{"selections":["S1.0"]}',
                    '{"selections":["S1.1","S1.1"]}', '{"selections":[{}]}',
                    '{"selections":null}', '{"selections":"S1.1"}', '["S1.1"]',
                    '{"selections":["S1.1"],"answer":"Uydurma"}',
                    '{"selections":[],"selections":["S1.1"]}',
                    'Açıklama {"selections":["S1.1"]}', 'print değer döndürmez. [S1]'):
            with self.subTest(raw=raw):
                result = self.ask(raw)
                self.assertEqual(result["status"], "invalid_evidence")
                self.assertEqual(result["evidence"], [])
                self.assertEqual(result["citations"], [])
                self.assertEqual(result["model_output"], raw)

    def test_empty_selection_is_abstention(self):
        result = self.ask('{"selections":[]}')
        self.assertEqual(result["status"], "model_abstained")
        self.assertEqual(result["answer"], FALLBACK)

    def test_native_empty_array_abstains_without_accepting_extra_claims(self):
        for raw in ('[]', ' [ ] ', '```json\n[]\n```'):
            with self.subTest(raw=raw):
                result = self.ask(raw)
                self.assertEqual(result["status"], "model_abstained")
                self.assertEqual(result["answer"], FALLBACK)
                self.assertEqual(result["model_output"], raw.strip())
        for raw in ('[] Ek iddia', 'null', '{}', '[[]]', '["S1.1"]'):
            with self.subTest(raw=raw):
                self.assertEqual(self.ask(raw)["status"], "invalid_evidence")

    def test_no_hits_skips_model(self):
        def fail(*args):
            raise AssertionError("Model çağrılmamalı")
        result = answer("Soru", SimpleNamespace(retrieve=lambda *a, **k: []), None,
                        SimpleNamespace(generate=fail), answer_mode="extractive")
        self.assertEqual(result["status"], "no_context")
        self.assertIsNone(result["generation_details"])

    def test_single_json_fence_accepted_extra_prose_rejected(self):
        self.assertEqual(len(parse_selection('```json\n{"selections":["S1.1"]}\n```', self.units)), 1)
        with self.assertRaises(ValueError):
            parse_selection('```json\n{"selections":[]}\n```\nEk iddia', self.units)

    def test_selection_limit_and_multiple_sources(self):
        hits = self.hits + [Hit(Chunk("ikinci.txt", 1, 0, "A. B. C. D. E."), .5)]
        units = evidence_units(hits)
        selected = parse_selection('{"selections":["S2.2","S1.2"]}', units)
        self.assertEqual([x["source_id"] for x in selected], [1, 2])
        with self.assertRaises(ValueError):
            parse_selection(json.dumps({"selections": list(units)[:7]}), units)

    def test_valid_id_is_not_a_semantic_correctness_claim(self):
        # Soruyu yanıtlamayan gerçek bir cümle bile biçim kontrolünden geçebilir.
        result = self.ask('{"selections":["S1.1"]}')
        self.assertEqual(result["evidence_validation"], "exact_source")
        self.assertNotIn("semantically_verified", result)


if __name__ == "__main__":
    unittest.main()
