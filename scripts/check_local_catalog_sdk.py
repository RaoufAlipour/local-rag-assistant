"""Gerçek SDK katalog ayrıştırıcısını sınar; model indirme/inference yapmaz.

Yalnız test metadata'sı kullanılır. Bu test çevrimdışı GPU cevap kabulü değildir.
"""
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ragapp.local_catalog import LocalCatalog
from foundry_local_sdk import Configuration, FoundryLocalManager

models = [{"id": "catalog-fixture-cpu:1", "name": "catalog-fixture-cpu", "version": 1,
           "alias": "catalog-fixture", "uri": "https://example.invalid/catalog-fixture",
           "task": "embeddings", "runtime": {"device_type": "CPU", "execution_provider": "CPUExecutionProvider"}}]
with tempfile.TemporaryDirectory() as directory, LocalCatalog(models) as catalog:
    FoundryLocalManager.initialize(Configuration(app_name="rag_catalog_adapter_test", app_data_dir=directory,
        catalog_urls=[(catalog.url, None)], catalog_region="centralus", disable_nonessential_telemetry=True))
    model = FoundryLocalManager.instance.catalog.get_model("catalog-fixture")
    assert model is not None, "SDK yerel katalog kaydını okuyamadı."
    assert model.id == models[0]["id"]
    assert model.info.task == "embeddings"
    assert model.info.runtime.execution_provider == "CPUExecutionProvider"
    assert catalog.requests > 0
    print("PASS: gerçek SDK yerel katalogdan model kimliği, görev ve CPU sağlayıcısını okudu.")
    print("Model ağırlığı indirilmedi veya yüklenmedi; GPU inference test edilmedi.")
