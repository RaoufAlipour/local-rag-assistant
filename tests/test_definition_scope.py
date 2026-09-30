import json
from types import SimpleNamespace
import unittest
from ragapp.core import Chunk, Hit, answer
from ragapp.evidence import evidence_units, scope_definition


class DefinitionTests(unittest.TestCase):
    def setUp(self):
        self.hits = [Hit(Chunk("dates.txt", 1, 0, "Tarih kontrol edilir. Ay uzunluğu önemlidir."), .38),
                     Hit(Chunk("api.txt", 1, 0, "flush tamponu boşaltır. flush değer döndürür. printable farklı bir addır."), .36)]
        self.store = SimpleNamespace(retrieve=lambda *args, **kwargs: self.hits)

    def test_unrelated_selection_removed_and_raw_preserved(self):
        raw = '{"selections":["S1.1","S1.2","S2.1"]}'
        def generate(system, user):
            offered = json.loads(user)["source_sentences"]
            self.assertEqual(set(offered), {"S2.1", "S2.2"})
            return raw
        result = answer("flush ne işe yarar", self.store, None, SimpleNamespace(generate=generate), answer_mode="extractive")
        self.assertEqual(result["answer"], "flush tamponu boşaltır. [S2]")
        self.assertEqual(result["model_output"], raw)
        self.assertEqual(result["citations"], [2])
        self.assertEqual(result["evidence_scope"]["excluded_ids"], ["S1.1", "S1.2"])

    def test_only_unrelated_selection_is_not_a_valid_answer(self):
        result = answer("flush nedir?", self.store, None,
                        SimpleNamespace(generate=lambda *a: '{"selections":["S1.1"]}'), answer_mode="extractive")
        self.assertEqual(result["status"], "invalid_evidence")
        self.assertEqual(result["citations"], [])

    def test_missing_identifier_skips_generation(self):
        def fail(*args):
            raise AssertionError("Model çağrılmamalı")
        result = answer("unlisted_api ne yapar?", self.store, None,
                        SimpleNamespace(generate=fail), answer_mode="extractive")
        self.assertEqual(result["status"], "no_context")
        self.assertIsNone(result["model_output"])

    def test_comparisons_and_long_questions_keep_context(self):
        units = evidence_units(self.hits)
        for question in ("print ile return aynı şey mi?", "Fonksiyonun dışında return yazarsam ne olur?",
                         "Python 4 hangi tarihte yayımlanacak?", "flush işleminin sonucu nedir?"):
            self.assertEqual(scope_definition(question, units), (units, None))

    def test_callable_spelling_and_whole_word_match(self):
        units = evidence_units(self.hits)
        self.assertEqual(set(scope_definition("Flush() ne işe yarar?", units)[0]), {"S2.1", "S2.2"})
        self.assertEqual(scope_definition("print nedir", units)[0], {})
