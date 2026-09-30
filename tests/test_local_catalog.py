from dataclasses import dataclass, field
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import urllib.request

from ragapp.evaluation import digest
from ragapp.foundry import Runtime
from ragapp.local_catalog import LocalCatalog, catalog_entry, filter_entries, validate_snapshot


@dataclass
class Info:
    id: str = "fixture-cpu:1"
    name: str = "fixture-cpu"
    version: int = 1
    alias: str = "fixture"
    uri: str = "https://example.invalid/fixture"
    task: str = "embeddings"
    runtime: dict = field(default_factory=lambda: {"device_type": "CPU", "execution_provider": "CPUExecutionProvider"})


class LocalCatalogTests(unittest.TestCase):
    def setUp(self):
        from dataclasses import asdict
        self.info = asdict(Info())
        self.snapshot = {"schema_version": 1, "sdk_version": "2.0.1", "device": "cpu",
                         "models": [self.info], "digest": digest([self.info])}

    def test_snapshot_rejects_wrong_device_and_altered_metadata(self):
        self.assertEqual(validate_snapshot(self.snapshot, "cpu"), [self.info])
        with self.assertRaises(ValueError):
            validate_snapshot(self.snapshot, "cuda")
        self.info["task"] = "chat-completion"
        with self.assertRaises(ValueError):
            validate_snapshot(self.snapshot, "cpu")

    def test_snapshot_rejects_missing_task_even_with_matching_digest(self):
        self.info["task"] = None
        self.snapshot["digest"] = digest([self.info])
        with self.assertRaises(ValueError):
            validate_snapshot(self.snapshot, "cpu")

    def test_filters_do_not_return_cpu_record_for_cuda_query(self):
        entry = catalog_entry(self.info)
        request = {"indexEntitiesRequest": {"filters": [{"field": "properties/variantInfo/variantMetadata/executionProvider",
                    "operator": "eq", "values": ["CUDAExecutionProvider"]}]}}
        self.assertEqual(filter_entries([entry], request), [])

    def test_loopback_catalog_preserves_id_and_task_and_closes(self):
        with LocalCatalog([self.info]) as catalog:
            self.assertEqual(catalog.server.server_address[0], "127.0.0.1")
            request = urllib.request.Request(catalog.url + "/entities/crossRegion",
                      data=b'{"indexEntitiesRequest":{"filters":[]}}', headers={"Content-Type": "application/json"})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request, timeout=3) as response:
                data = json.load(response)
            record = data["indexEntitiesResponse"]["value"][0]
            self.assertEqual(record["annotations"]["tags"]["task"], "embeddings")
            self.assertEqual(record["properties"]["id"], self.info["id"])
            self.assertEqual(catalog.requests, 1)
        self.assertFalse(catalog.thread.is_alive())

    def test_snapshot_command_does_not_download_or_load_weights(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime.__new__(Runtime)
            runtime.device, runtime.offline = "cpu", False
            runtime.snapshot_path = Path(directory) / "snapshot.json"
            # No load/download methods: snapshot must only inspect metadata and cache status.
            runtime.model = lambda alias: SimpleNamespace(is_cached=True, info=Info())
            runtime.snapshot(["fixture"])
            saved = json.loads(runtime.snapshot_path.read_text())
            self.assertEqual(validate_snapshot(saved, "cpu")[0]["id"], "fixture-cpu:1")

    def test_incomplete_snapshot_does_not_replace_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime.__new__(Runtime)
            runtime.device, runtime.offline = "cpu", False
            runtime.snapshot_path = Path(directory) / "snapshot.json"
            runtime.snapshot_path.write_text("previous")
            runtime.model = lambda alias: SimpleNamespace(is_cached=False, info=Info())
            with self.assertRaises(ValueError):
                runtime.snapshot(["fixture"])
            self.assertEqual(runtime.snapshot_path.read_text(), "previous")
