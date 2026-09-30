import json
from types import SimpleNamespace
import unittest
from ragapp.core import Chunk, Hit, answer, FALLBACK
from ragapp.evidence import evidence_units, scope_event_date


class EventDateTests(unittest.TestCase):
    def ask(self, question, content, output, should_generate=True):
        def generate(system, user):
            self.assertTrue(should_generate)
            self.offered = json.loads(user)["source_sentences"]
            return output
        hits = [Hit(Chunk("program.pdf", 1, 0, content), .8)]
        return answer(question, SimpleNamespace(retrieve=lambda *a, **k: hits), None,
                      SimpleNamespace(generate=generate), answer_mode="extractive")

    def test_document_date_is_not_an_event_date(self):
        result = self.ask("Toplantı tarihi nedir?", "Belge sürümü 29 Eylül 2026. Proje kurgusaldır.",
                          None, should_generate=False)
        self.assertEqual(result["status"], "no_context")
        self.assertEqual(result["answer"], FALLBACK)
        self.assertIsNone(result["generation_details"])
        self.assertEqual(result["evidence_scope"]["rule"], "event_date")

    def test_correct_date_survives_different_document_date(self):
        result = self.ask("Etkinliğin toplantı tarihi nedir?",
                          "Belge 29 Eylül 2026 günü hazırlandı. Toplantı 7 Ekim 2026 günü yapılır.",
                          '{"selections":["S1.1","S1.2"]}')
        self.assertEqual(result["answer"], "Toplantı 7 Ekim 2026 günü yapılır. [S1]")
        self.assertEqual(set(self.offered), {"S1.2"})
        self.assertEqual(result["evidence_scope"]["excluded_ids"], ["S1.1"])

    def test_event_without_date_cannot_borrow_header_date(self):
        result = self.ask("Teslim tarihi nedir?", "Sürüm tarihi 29 Eylül 2026. Teslim bilgisi açıklanmamıştır.",
                          None, should_generate=False)
        self.assertEqual(result["status"], "no_context")

    def test_merged_pdf_heading_date_not_used_for_event_description(self):
        for text in ("Sürüm 1.0 / 29 Eylül 2026 Toplantı için gerekli belgeler listelenmiştir.",
                     "Toplantı rehberi Belge tarihi 29 Eylül 2026 katılım koşulları aşağıdadır."):
            result = self.ask("Toplantı tarihi nedir?", text, None, should_generate=False)
            self.assertEqual(result["status"], "no_context")

    def test_date_before_event_with_explicit_relation(self):
        result = self.ask("Toplantı tarihi nedir?", "7 Ekim 2026 tarihinde toplantı yapılacaktır.",
                          '{"selections":["S1.1"]}')
        self.assertEqual(result["status"], "answered")

    def test_possessive_event_and_numeric_dates(self):
        for question in ("Projenin teslimi hangi tarihte yapılacak?", "Teslim tarihi nedir?"):
            result = self.ask(question, "Teslim 2026-11-07 tarihinde yapılır.", '{"selections":["S1.1"]}')
            self.assertEqual(result["status"], "answered")

    def test_unrelated_selected_id_rejected(self):
        result = self.ask("Toplantı tarihi nedir?", "Belge 29 Eylül 2026. Toplantı 7 Ekim 2026.",
                          '{"selections":["S1.1"]}')
        self.assertEqual(result["status"], "invalid_evidence")
        self.assertEqual(result["citations"], [])

    def test_other_questions_and_multiple_events_not_narrowed(self):
        units = evidence_units([Hit(Chunk("note", 1, 0, "Belge tarihi 1 Ekim 2026."), .8)])
        for question in ("Yedekler kaç gün saklanır?", "Toplantı ve teslim tarihi nedir?",
                         "Python 4 hangi tarihte yayımlanacak?", "Bu kod ne yapar?"):
            self.assertEqual(scope_event_date(question, units), (units, None))
