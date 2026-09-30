import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from ragapp.foundry import Runtime, register_device


def ep(registered):
    return SimpleNamespace(name="CUDAExecutionProvider", is_registered=registered)


def model(provider, cached=True):
    return SimpleNamespace(alias="example", id=f"example-{provider}:1", is_cached=cached,
                           info=SimpleNamespace(task="chat-completion",
                                                runtime=SimpleNamespace(execution_provider=provider)))


class DeviceTests(unittest.TestCase):
    def test_each_new_process_manager_needs_registration(self):
        for _ in range(2):
            manager = Mock()
            manager.discover_eps.side_effect = [[ep(False)], [ep(True)]]
            manager.download_and_register_eps.return_value = SimpleNamespace(success=True)
            register_device(manager, "cuda")
            manager.download_and_register_eps.assert_called_once_with(names=["CUDAExecutionProvider"])

    def test_already_registered_provider_is_reused(self):
        manager = Mock()
        manager.discover_eps.return_value = [ep(True)]
        register_device(manager, "cuda")
        manager.download_and_register_eps.assert_not_called()

    def test_reported_success_without_active_cuda_is_rejected(self):
        manager = Mock()
        manager.discover_eps.return_value = [ep(False)]
        manager.download_and_register_eps.return_value = SimpleNamespace(success=True)
        with self.assertRaises(RuntimeError):
            register_device(manager, "cuda")

    def test_missing_cuda_does_not_download_other_providers(self):
        manager = Mock()
        manager.discover_eps.return_value = []
        with self.assertRaises(ValueError):
            register_device(manager, "cuda")
        manager.download_and_register_eps.assert_not_called()

    def test_cpu_mode_does_not_request_provider_downloads(self):
        manager = Mock()
        register_device(manager, "cpu")
        manager.discover_eps.assert_not_called()
        manager.download_and_register_eps.assert_not_called()

    def test_old_cpu_mapping_does_not_override_cuda_request(self):
        cpu, gpu = model("CPUExecutionProvider"), model("CUDAExecutionProvider", False)
        cpu.variants = [cpu, gpu]
        def select(variant):
            cpu.id, cpu.info = variant.id, variant.info
        cpu.select_variant = select
        runtime = Runtime.__new__(Runtime)
        runtime.device = "cuda"
        runtime.model_map = {"example": cpu.id}
        runtime.manager = SimpleNamespace(catalog=SimpleNamespace(
            get_cached_models=lambda: [cpu], get_model=lambda alias: cpu))
        result = runtime.model("example")
        self.assertEqual(result.id, gpu.id)
        self.assertEqual(result.info.runtime.execution_provider, "CUDAExecutionProvider")

    def test_cuda_request_rejects_cpu_only_catalog(self):
        cpu = model("CPUExecutionProvider")
        cpu.variants = [cpu]
        runtime = Runtime.__new__(Runtime)
        runtime.device = "cuda"
        with self.assertRaises(ValueError):
            runtime.select_device(cpu)

    def test_device_preference_commits_only_after_model_preparation(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime.__new__(Runtime)
            runtime.device = "cuda"
            runtime.model_map = {}
            runtime.model_map_path = Path(temp) / "models.json"
            runtime.settings_path = Path(temp) / "settings.json"
            gpu = model("CUDAExecutionProvider")
            gpu.download = Mock(side_effect=RuntimeError("download failed"))
            runtime.model = lambda alias: gpu
            with self.assertRaises(RuntimeError):
                runtime.prepare(["example"])
            self.assertFalse(runtime.settings_path.exists())
            gpu.download.side_effect = None
            runtime.prepare(["example"])
            self.assertEqual(json.loads(runtime.settings_path.read_text()), {"device": "cuda"})
