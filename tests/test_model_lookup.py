from types import SimpleNamespace
import unittest
from ragapp.foundry import Runtime


class ModelLookupTests(unittest.TestCase):
    def setUp(self):
        self.cached = SimpleNamespace(id="qwen-example-generic-cpu:1", alias="qwen-example-generic-cpu",
                                      info=SimpleNamespace(task="embeddings", runtime=SimpleNamespace(execution_provider="CPUExecutionProvider")))
        self.runtime = Runtime.__new__(Runtime)
        self.runtime.device = "cpu"
        self.runtime.model_map = {"qwen-example": self.cached.id}
        def unavailable(alias):
            self.fail("Cached model should not require online lookup")
        self.runtime.manager = SimpleNamespace(catalog=SimpleNamespace(
            get_cached_models=lambda: [self.cached], get_model=unavailable))

    def test_public_alias_uses_recorded_variant_offline(self):
        self.assertIs(self.runtime.model("qwen-example"), self.cached)

    def test_explicit_variant_id_works_without_mapping(self):
        self.runtime.model_map = {}
        self.assertIs(self.runtime.model(self.cached.id), self.cached)

    def test_unavailable_model_is_not_silently_substituted(self):
        self.runtime.manager.catalog.get_model = lambda alias: None
        with self.assertRaises(ValueError):
            self.runtime.model("another-model")

    def test_incomplete_cached_metadata_is_not_passed_to_session(self):
        self.cached.info.task = None
        self.runtime.manager.catalog.get_model = lambda alias: None
        with self.assertRaises(ValueError):
            self.runtime.model("qwen-example")
