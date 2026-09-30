"""AppTest akış kontrolleri; GPU çalıştırmaz ve görsel tarayıcı testi değildir."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
import unittest

HAS_STREAMLIT = importlib.util.find_spec("streamlit") is not None
ROOT = Path(__file__).resolve().parents[1]


class FakeService:
    def inventory(self):
        return [{"Belge": "ders.txt", "Parça": 1}]

    def ask(self, question, mode):
        return {"question": question, "answer": "<b>Metin aynen</b> [S1]", "status": "answered",
                "answer_mode": mode, "citations": [1], "total_seconds": 1.25,
                "retrieved": [{"id": "S1", "chunk": {"source": "ders.txt", "page": 1,
                               "content": "Tam kaynak metni."}}]}


@unittest.skipUnless(HAS_STREAMLIT, "İsteğe bağlı requirements-ui.txt kurulu değil")
class UiTests(unittest.TestCase):
    def setUp(self):
        import streamlit as st
        st.cache_resource.clear()

    def run_app(self):
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file(str(ROOT / "app.py")).run()

    def test_chat_rerun_preserves_history_and_shows_literal_source(self):
        with patch("ragapp.ui_service.LocalService", return_value=FakeService()):
            app = self.run_app()
            self.assertFalse(app.exception)
            app.chat_input[0].set_value("Sorum").run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state["history"]), 1)
            self.assertTrue(any(t.value == "<b>Metin aynen</b> [S1]" for t in app.text))
            self.assertTrue(any(t.value == "Tam kaynak metni." for t in app.text))
            app.button[0].click().run()
            self.assertEqual(app.session_state["history"], [])

    def test_documents_page(self):
        with patch("ragapp.ui_service.LocalService", return_value=FakeService()):
            app = self.run_app()
            app.radio[0].set_value("Belgeler").run()
            self.assertFalse(app.exception)
            self.assertTrue(any(t.value == "Bilgi kaynağın" for t in app.title))
            self.assertEqual(len(app.dataframe), 1)
            self.assertEqual(len(app.get("file_uploader")), 1)

    def test_missing_index_disables_question_input(self):
        service = FakeService()
        service.inventory = lambda: []
        with patch("ragapp.ui_service.LocalService", return_value=service):
            app = self.run_app()
            self.assertFalse(app.exception)
            self.assertTrue(app.chat_input[0].disabled)

    def test_backend_error_does_not_create_fake_answer(self):
        service = FakeService()
        service.ask = lambda *args: (_ for _ in ()).throw(ValueError("Model yok"))
        with patch("ragapp.ui_service.LocalService", return_value=service):
            app = self.run_app()
            app.chat_input[0].set_value("Sorum").run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["history"], [])
            self.assertIn("Model yok", app.error[0].value)


if __name__ == "__main__":
    unittest.main()
