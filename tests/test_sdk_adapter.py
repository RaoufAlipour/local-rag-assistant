"""SDK kuruluysa çalışır; model veya ağ erişimi gerektirmez."""
import importlib.util
import unittest
from ragapp.foundry import response_text


@unittest.skipUnless(importlib.util.find_spec("foundry_local_sdk"), "Foundry SDK kurulu değil")
class NativeResponseTests(unittest.TestCase):
    def test_assistant_message_parts_are_read(self):
        from foundry_local_sdk import MessageItem, TextItem
        message = MessageItem.assistant([TextItem("Merhaba "), TextItem("[S1]")])
        self.assertEqual(response_text([message]), "Merhaba [S1]")

    def test_direct_text_response_is_read(self):
        from foundry_local_sdk import TextItem
        self.assertEqual(response_text([TextItem("Merhaba")]), "Merhaba")
