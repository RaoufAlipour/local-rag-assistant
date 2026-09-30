"""Arayüz için tek işçi: SDK ve indeks yazımları aynı iş parçacığında sıraya girer."""
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from copy import deepcopy
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import time
from ragapp.core import Store, answer, read_pages


class LocalService:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.db = self.root / "storage/knowledge.db"
        self.documents = self.root / "data/documents"
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rag-model")
        self.runtime = self.embedder = self.generator = None
        self.answers = OrderedDict()

    def _index_signature(self):
        digest = hashlib.sha256()
        for path in (self.db, Path(str(self.db) + "-wal")):
            digest.update(path.name.encode())
            if path.is_file():
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
        return digest.hexdigest()

    def inventory(self):
        if not self.db.is_file():
            return []
        with sqlite3.connect(self.db.as_uri() + "?mode=ro", uri=True) as db:
            return [{"Belge": source, "Parça": count} for source, count in db.execute(
                "SELECT source,count(*) FROM chunks GROUP BY source ORDER BY source")]

    def _engine(self):
        if self.runtime is None:
            from ragapp.foundry import Runtime, FoundryEmbedder, FoundryGenerator
            # Model hazırlama indirme veya ağ kataloğuna geri dönüş yok.
            self.runtime = Runtime(offline=True)
        if self.embedder is None:
            self.embedder = FoundryEmbedder(self.runtime, "qwen3-embedding-0.6b")
        if self.generator is None:
            self.generator = FoundryGenerator(self.runtime, "qwen2.5-7b")

    def ask(self, question, mode="extractive"):
        return self.worker.submit(self._ask, question, mode).result()

    def _ask(self, question, mode):
        started = time.perf_counter()
        if not self.db.is_file():
            raise ValueError("Önce Belgeler bölümünden notlarını indekse ekle.")
        question = question.strip()
        key = (question, mode, self._index_signature())
        if key in self.answers:
            cached = deepcopy(self.answers[key])
            self.answers.move_to_end(key)
            cached.update(cache_hit=True, cached_original_seconds=cached["total_seconds"],
                          generation_details=None, retrieval_seconds=0.0, generation_seconds=0.0,
                          total_seconds=round(time.perf_counter()-started, 4))
            return cached
        self._engine()
        with Store(self.db) as store:
            result = answer(question, store, self.embedder, self.generator,
                            retrieval_mode="hybrid", answer_mode=mode)
        result["cache_hit"] = False
        if result["status"] in {"answered", "no_context", "model_abstained"}:
            self.answers[key] = deepcopy(result)
            if len(self.answers) > 32:
                self.answers.popitem(last=False)
        return result

    def ingest(self, uploads=()):
        """uploads: (ad, bytes). Var olan dosyaları değiştirme; hatada yenileri geri al."""
        return self.worker.submit(self._ingest, uploads).result()

    def _ingest(self, uploads):
        staged = []
        names = set()
        target = self.documents / "uploads"
        if not target.resolve().is_relative_to(self.documents.resolve()):
            raise ValueError("Yükleme klasörü belge klasörünün dışında olamaz.")
        with tempfile.TemporaryDirectory(prefix="rag-upload-") as temporary:
            for name, data in uploads:
                # Windows ve POSIX yolları; alternatif veri akışları da kabul edilmez.
                if (not name or name != Path(name).name or any(c in name for c in '/\\:')
                        or name.endswith((' ', '.')) or name.startswith('.')
                        or Path(name).suffix.lower() not in {".txt", ".md", ".pdf"}):
                    raise ValueError("Dosya adı veya türü desteklenmiyor: " + name)
                if name.casefold() in names or (target / name).exists():
                    raise ValueError("Aynı adlı dosya var; yeni belgeye farklı bir ad ver: " + name)
                if not data or len(data) > 20 * 1024 * 1024:
                    raise ValueError("Her belge boş olmayan, en fazla 20 MB bir dosya olmalı.")
                names.add(name.casefold())
                path = Path(temporary) / name
                path.write_bytes(data)
                pages = read_pages(path)
                if not any(text.strip() for _, text in pages):
                    raise ValueError("Belgede okunabilir metin yok: " + name)
                staged.append((target / name, data))
            self._engine()
            created = []
            try:
                if staged:
                    target.mkdir(parents=True, exist_ok=True)
                for path, data in staged:
                    # Son kontrol ile yazım arasındaki çakışmada da dosya ezilmez.
                    with path.open("xb") as stream:
                        created.append(path)
                        stream.write(data)
                with Store(self.db) as store:
                    result = store.ingest(self.documents, self.embedder)
                self.answers.clear()
                return result
            except BaseException:
                for path in created:
                    path.unlink(missing_ok=True)
                raise
