"""Belge eklemede veri kaybı ve SDK iş parçacığı sınırını kontrol eder."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from ragapp.ui_service import LocalService


class ServiceTests(unittest.TestCase):
    def test_identical_question_reuses_answer_without_model_and_is_not_mutable(self):
        self.service.ingest([("not.txt", b"Python belge.")])
        first = self.service.ask("Python?")
        calls = len(self.threads)
        first["answer"] = "Dışarıdan değiştirildi"
        cached = self.service.ask("Python?")
        self.assertEqual(len(self.threads), calls)
        self.assertTrue(cached["cache_hit"])
        self.assertEqual(cached["answer"], "Python belge. [S1]")
        self.assertIsNone(cached["generation_details"])
        self.assertEqual(cached["generation_seconds"], 0)

    def test_index_change_invalidates_cached_answer(self):
        self.service.ingest([("not.txt", b"Python belge.")])
        self.service.ask("Python?")
        from ragapp.core import Store
        with Store(self.service.db) as store:
            with store.db:
                store.db.execute("UPDATE chunks SET content=?", ("Python yeni bilgi.",))
        result = self.service.ask("Python?")
        self.assertFalse(result["cache_hit"])
        self.assertEqual(result["answer"], "Python yeni bilgi. [S1]")

    def test_answer_mode_and_cache_capacity_are_respected(self):
        self.service.ingest([("not.txt", b"Python belge.")])
        self.service.ask("Python?")
        result = self.service.ask("Python?", mode="generative")
        self.assertFalse(result["cache_hit"])
        for i in range(35):
            self.service.ask(f"Python soru {i}?")
        self.assertEqual(len(self.service.answers), 32)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.service = LocalService(self.temporary.name)
        self.service.documents.mkdir(parents=True)
        self.threads = []
        embedder = SimpleNamespace(identity="ui-test", embed=lambda texts: [[1, 0] for _ in texts],
                                   embed_query=lambda text: [1, 0])
        def engine():
            self.threads.append(threading.get_ident())
            self.service.embedder = embedder
            self.service.generator = SimpleNamespace(generate=lambda *args: '{"selections":["S1.1"]}')
        self.service._engine = engine

    def tearDown(self):
        self.service.worker.shutdown(wait=True)
        self.temporary.cleanup()

    def test_new_document_indexed_and_existing_upload_not_overwritten(self):
        self.service.ingest([("not.txt", b"Python belge.")])
        self.assertEqual(self.service.inventory(), [{"Belge": "uploads/not.txt", "Parça": 1}])
        with self.assertRaises(ValueError):
            self.service.ingest([("not.txt", b"Degisen.")])
        self.assertEqual((self.service.documents / "uploads/not.txt").read_bytes(), b"Python belge.")

    def test_invalid_file_or_path_does_not_initialize_engine(self):
        for name, data in [("../x.txt", b"x"), ("..\\x.txt", b"x"), ("x.txt:evil", b"x"),
                           ("x.txt", b""), ("x.pdf", b"not a PDF"), ("x.txt", b"\xff")]:
            with self.subTest(name=name), self.assertRaises(Exception):
                self.service.ingest([(name, data)])
        self.assertEqual(self.threads, [])
        self.assertFalse(self.service.db.exists())

    def test_failed_embedding_rolls_back_new_files_and_preserves_index(self):
        self.service.ingest([("old.txt", b"Python eski.")])
        before = self.service.inventory()
        self.service._engine = lambda: None
        self.service.embedder.embed = lambda texts: []
        with self.assertRaises(ValueError):
            self.service.ingest([("new.txt", b"Python yeni.")])
        self.assertFalse((self.service.documents / "uploads/new.txt").exists())
        self.assertEqual(self.service.inventory(), before)

    def test_concurrent_calls_use_one_worker_and_retrieval_works(self):
        self.service.ingest([("not.txt", b"Python belge.")])
        with ThreadPoolExecutor(max_workers=2) as callers:
            results = list(callers.map(self.service.ask, ["Python?", "Belge?"]))
        self.assertTrue(all(r["answer"] == "Python belge. [S1]" for r in results))
        self.assertEqual(len(set(self.threads)), 1)
        self.assertNotEqual(self.threads[0], threading.get_ident())


if __name__ == "__main__":
    unittest.main()
