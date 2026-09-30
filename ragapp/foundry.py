"""Foundry Local 2.0.1 native session bağlantısı. Bulut API'si kullanmaz."""
import math
import struct
import json
import sys
import time
from pathlib import Path


PROVIDERS = {"cpu": "CPUExecutionProvider", "cuda": "CUDAExecutionProvider"}


class TimedContext:
    """SDK context manager davranışını koruyarak açılış/kapanış süresini ayırır."""
    def __init__(self, factory, name, timings):
        self.factory, self.name, self.timings = factory, name, timings

    def __enter__(self):
        start = time.perf_counter()
        try:
            self.context = self.factory()
            return self.context.__enter__()
        finally:
            self.timings[self.name + "_open_seconds"] = round(time.perf_counter() - start, 6)

    def __exit__(self, *exception):
        start = time.perf_counter()
        try:
            return self.context.__exit__(*exception)
        finally:
            self.timings[self.name + "_close_seconds"] = round(time.perf_counter() - start, 6)


def register_device(manager, device):
    """EP registration belongs to this process. SDK may access the network here."""
    if device not in PROVIDERS:
        raise ValueError("device cpu veya cuda olmalı.")
    if device == "cpu":
        return
    name = PROVIDERS[device]
    before = {e.name: e.is_registered for e in manager.discover_eps()}
    if name not in before:
        raise ValueError("CUDA bileşeni bu ortamda bulunamadı; CPU'ya geçilmedi.")
    if not before[name]:
        result = manager.download_and_register_eps(names=[name])
        after = {e.name: e.is_registered for e in manager.discover_eps()}
        if not result.success or not after.get(name, False):
            raise RuntimeError("CUDA bu süreçte kaydedilemedi; CPU'ya geçilmedi.")


def response_text(response):
    """Native cevap MessageItem içinde TextItem döndürebilir."""
    from foundry_local_sdk import MessageItem, TextItem
    texts = []
    for item in response:
        if isinstance(item, TextItem):
            texts.append(item.text)
        elif isinstance(item, MessageItem):
            texts.extend(part.text for part in item.parts if isinstance(part, TextItem))
    return "".join(texts)


def tensor_vector(tensor):
    """SDK 2.0.1 TensorItem.data alanı float listesi değil, bytes döndürür."""
    formats = {"FLOAT": "f", "FLOAT16": "e", "DOUBLE": "d"}
    fmt = formats.get(tensor.data_type.name)
    if fmt is None:
        raise ValueError(f"Desteklenmeyen embedding türü: {tensor.data_type.name}")
    count = math.prod(tensor.shape)
    if count < 1 or len(tensor.data) != count * struct.calcsize(fmt):
        raise ValueError("Model geçersiz embedding tensorü döndürdü.")
    if len(tensor.shape) > 1 and math.prod(tensor.shape[:-1]) != 1:
        raise ValueError("Her metin için tek embedding vektörü bekleniyor.")
    return list(struct.unpack(f"={count}{fmt}", tensor.data))


class Runtime:
    def __init__(self, device=None, offline=False):
        self.settings_path = Path(__file__).resolve().parents[1] / "storage/runtime-settings.json"
        settings = (json.loads(self.settings_path.read_text(encoding="utf-8"))
                    if self.settings_path.exists() else {})
        self.device = device if device is not None else settings.get("device", "cpu")
        if self.device not in PROVIDERS:
            raise ValueError("device cpu veya cuda olmalı.")
        self.offline = offline
        self.local_catalog = None
        self.snapshot_path = self.settings_path.parent / "offline-models.json"
        from foundry_local_sdk import Configuration, FoundryLocalManager
        self.loaded = []
        try:
            options = {}
            if offline:
                from ragapp.local_catalog import LocalCatalog, validate_snapshot
                if FoundryLocalManager.instance is not None:
                    raise ValueError("--offline yeni bir Python sürecinde başlatılmalı.")
                if not self.snapshot_path.is_file():
                    raise ValueError("Yerel katalog yok. İnternet açıkken snapshot --chat-model MODEL çalıştırın.")
                models = validate_snapshot(json.loads(self.snapshot_path.read_text(encoding="utf-8")), self.device)
                self.local_catalog = LocalCatalog(models)
                # Explicit custom catalog URL: only this loopback metadata service is used.
                options = {"catalog_urls": [(self.local_catalog.url, None)], "catalog_region": "centralus"}
            if FoundryLocalManager.instance is None:
                FoundryLocalManager.initialize(Configuration(app_name="python_notes_rag", disable_nonessential_telemetry=True, **options))
            self.manager = FoundryLocalManager.instance
            # EP registration still uses the SDK and must also work with internet disconnected.
            register_device(self.manager, self.device)
        except BaseException:
            if self.local_catalog is not None:
                self.local_catalog.close()
            raise
        self.model_map_path = Path(__file__).resolve().parents[1] / "storage/model-map.json"
        self.model_map = (json.loads(self.model_map_path.read_text(encoding="utf-8"))
                          if self.model_map_path.exists() else {})

    @staticmethod
    def describe(model):
        info = model.info
        backend = info.runtime
        return {"alias": model.alias, "id": model.id, "task": info.task,
                "cached": model.is_cached,
                "device_type": str(backend.device_type) if backend and backend.device_type else None,
                "execution_provider": backend.execution_provider if backend else None,
                "file_size_mb": info.file_size_mb}

    def matches_device(self, model):
        backend = model.info.runtime
        return backend is not None and backend.execution_provider == PROVIDERS[self.device]

    def select_device(self, model):
        if self.matches_device(model):
            return model
        for variant in model.variants:
            if self.matches_device(variant):
                model.select_variant(variant)
                if self.matches_device(model):
                    return model
                break
        raise ValueError(f"{model.alias}: {self.device} için uygun varyant seçilemedi; başka cihaza geçilmedi.")

    def models(self, aliases=None):
        result = []
        for model in self.manager.catalog.list_models():
            if aliases is not None and model.alias not in aliases:
                continue
            compatible = any(self.matches_device(v) for v in model.variants) or self.matches_device(model)
            if compatible:
                self.select_device(model)
            result.append({**self.describe(model), "requested_device": self.device,
                           "requested_device_available": compatible, "capabilities": model.capabilities,
                           "variants": [self.describe(v) for v in model.variants]})
        return result

    def model(self, alias):
        # Offline cached models expose variant names, not always public catalog aliases.
        # Match the exact ID recorded by prepare; never infer a different hardware variant.
        cached_id = self.model_map.get(alias, alias)
        for cached in self.manager.catalog.get_cached_models():
            if cached.id == cached_id and cached.info.task is not None and self.matches_device(cached):
                return cached
        model = self.manager.catalog.get_model(alias)
        if model is None:
            raise ValueError(f"Modelin tam katalog bilgisi bulunamadı: {alias}. "
                             "Model dosyaları hazırsa çevrimiçi snapshot komutuyla katalog bilgisini "
                             "kaydedip yeni süreçte --offline kullanın; tekrar ağırlık indirmeyin.")
        return self.select_device(model)

    def snapshot(self, aliases):
        """Capture actual, complete catalog metadata without downloading/loading weights."""
        from dataclasses import asdict
        from ragapp.evaluation import digest, save_json
        if self.offline:
            raise ValueError("snapshot internet açıkken hazırlanmalıdır.")
        models = []
        for alias in aliases:
            model = self.model(alias)
            if not model.is_cached:
                raise ValueError(f"{alias}: model dosyaları henüz hazır değil; önce prepare gerekir.")
            models.append(asdict(model.info))
        value = {"schema_version": 1, "sdk_version": "2.0.1", "device": self.device,
                 "models": models, "digest": digest(models)}
        from ragapp.local_catalog import validate_snapshot
        validate_snapshot(value, self.device)
        save_json(self.snapshot_path, value)
        print(f"Yerel katalog kaydedildi: {self.snapshot_path}")
        print("Model ağırlıkları yeniden indirilmedi. Sonraki ağsız komuta --offline ekleyin.")

    def prepare(self, aliases):
        # Model weights are downloaded only here. The selected EP is registered at startup.
        for alias in aliases:
            model = self.model(alias)
            model.download(lambda p: print(f"\r{alias}: %{p:.1f}", end="", flush=True))
            print()
            if not model.is_cached:
                raise ValueError(f"Model indirmesi doğrulanamadı: {alias}")
            if not self.matches_device(model):
                raise ValueError(f"{alias}: indirme sonrası seçilen cihaz değişti; ayar kaydedilmedi.")
            from ragapp.evaluation import save_json
            self.model_map[alias] = model.id
            save_json(self.model_map_path, self.model_map)
            print(f"Hazır: {alias} -> {model.id}", flush=True)
        from ragapp.evaluation import save_json
        save_json(self.settings_path, {"device": self.device})
        print(f"Sonraki açılışlar için cihaz kaydedildi: {self.device}", flush=True)

    def load(self, alias):
        self.last_load_timings = {}
        start = time.perf_counter()
        model = self.model(alias)
        self.last_load_timings["catalog_lookup_seconds"] = round(time.perf_counter() - start, 6)
        start = time.perf_counter()
        cached = model.is_cached
        self.last_load_timings["cached_state_seconds"] = round(time.perf_counter() - start, 6)
        if not cached:
            raise ValueError(f"Model henüz indirilmedi: {alias}. Önce prepare komutunu çalıştırın.")
        start = time.perf_counter()
        loaded = model.is_loaded
        self.last_load_timings["loaded_state_seconds"] = round(time.perf_counter() - start, 6)
        self.last_load_timings["model_load_seconds"] = 0.0
        self.last_load_timings["model_log_seconds"] = 0.0
        if not loaded:
            start = time.perf_counter()
            model.load()
            self.last_load_timings["model_load_seconds"] = round(time.perf_counter() - start, 6)
            self.loaded.append(model)
            # Metadata describes the selected variant; it is not a GPU profiler result.
            start = time.perf_counter()
            print("Yüklenen model: " + json.dumps(self.describe(model), ensure_ascii=False), file=sys.stderr)
            self.last_load_timings["model_log_seconds"] = round(time.perf_counter() - start, 6)
        return model

    def close(self):
        try:
            for model in reversed(self.loaded):
                model.unload()
            self.loaded.clear()
        finally:
            catalog = getattr(self, "local_catalog", None)
            if catalog is not None:
                catalog.close()
                self.local_catalog = None


class FoundryEmbedder:
    def __init__(self, runtime, alias):
        self.model = runtime.load(alias)
        self.identity = f"foundry-2.0.1:{self.model.id}:query-instruction-v1"

    def embed(self, texts):
        from foundry_local_sdk import EmbeddingsSession, Request, TextItem, TensorItem
        with EmbeddingsSession(self.model) as session, Request() as request:
            for text in texts:
                request.add_item(TextItem(text))
            with session.process_request(request) as response:
                vectors = [tensor_vector(item) for item in response if isinstance(item, TensorItem)]
        if len(vectors) != len(texts):
            raise ValueError("Embedding sayısı giriş metinleriyle eşleşmiyor.")
        return vectors

    def embed_query(self, text):
        # Qwen3 embedding sorgu yönergesi; belgelere uygulanmaz.
        prompt = "Instruct: Given a question, retrieve relevant passages that answer the question\nQuery: " + text
        return self.embed([prompt])[0]


class FoundryGenerator:
    def __init__(self, runtime, alias):
        self.runtime, self.alias = runtime, alias
        self.last_timings = {}

    def generate(self, system, user, max_output_tokens=192):
        if isinstance(max_output_tokens, bool) or not isinstance(max_output_tokens, int) or not 1 <= max_output_tokens <= 4096:
            raise ValueError("Çıktı sınırı 1–4096 arasında bir tam sayı olmalı.")
        from foundry_local_sdk import ChatSession, Request, RequestOptions, SearchOptions, MessageItem, TextItem
        self.last_timings = timings = {"max_output_tokens": max_output_tokens,
                                      "prompt_characters": len(system) + len(user)}
        start = time.perf_counter()
        model = self.runtime.load(self.alias)
        timings["model_lookup_and_load_seconds"] = round(time.perf_counter() - start, 6)
        timings["model_details"] = dict(self.runtime.last_load_timings)
        # Her soru için yeni session: önceki cevap yeni sorunun kaynağı olmaz.
        with TimedContext(lambda: ChatSession(model), "session", timings) as session, TimedContext(Request, "request", timings) as request:
            setup_start = time.perf_counter()
            session.set_options(RequestOptions(search=SearchOptions(
                temperature=0.0, do_sample=False, max_output_tokens=max_output_tokens)))
            request.add_item(MessageItem.system(system))
            request.add_item(MessageItem.user(user))
            timings["request_setup_seconds"] = round(time.perf_counter() - setup_start, 6)
            with TimedContext(lambda: session.process_request(request), "response", timings) as response:
                read_start = time.perf_counter()
                result = response_text(response)
                timings["response_read_seconds"] = round(time.perf_counter() - read_start, 6)
        timings["total_seconds"] = round(time.perf_counter() - start, 6)
        timings["output_characters"] = len(result)
        timings["trailing_whitespace_characters"] = len(result) - len(result.rstrip())
        if not result.strip():
            raise ValueError("Model boş cevap döndürdü.")
        return result
