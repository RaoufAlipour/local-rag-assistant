from contextlib import contextmanager
import unittest
from ragapp.foundry import TimedContext


class TimingTests(unittest.TestCase):
    def test_exception_still_closes_resource_and_propagates(self):
        events, timings = [], {}

        @contextmanager
        def resource():
            try:
                events.append("opened")
                yield "value"
            finally:
                events.append("closed")

        with self.assertRaisesRegex(ValueError, "failure"):
            with TimedContext(resource, "resource", timings) as value:
                self.assertEqual(value, "value")
                raise ValueError("failure")
        self.assertEqual(events, ["opened", "closed"])
        self.assertGreaterEqual(timings["resource_open_seconds"], 0)
        self.assertGreaterEqual(timings["resource_close_seconds"], 0)

    def test_underlying_exception_suppression_is_preserved(self):
        @contextmanager
        def resource():
            try:
                yield
            except ValueError:
                pass

        with TimedContext(resource, "resource", {}):
            raise ValueError("suppressed by original context")
