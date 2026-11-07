import os
import unittest
from unittest.mock import patch
from core.llm_router_v2 import route, ModelUnavailable


class ChatGatewayRouterTests(unittest.TestCase):
    def test_emergency_not_called_by_default(self):
        called = []
        def fake(endpoint, model, prompt, timeout):
            called.append(model)
            raise OSError("unavailable")
        with patch.dict(os.environ, {"MONOLITH_LLM_EMERGENCY_ENABLED": "false"}):
            with self.assertRaises(ModelUnavailable):
                route("hello", primary="main-model", secondary="", generator=fake)
        self.assertEqual(called, ["main-model"])

    def test_response_includes_actual_model(self):
        def fake(endpoint, model, prompt, timeout):
            return "real output from " + model
        with patch.dict(os.environ, {"MONOLITH_LLM_EMERGENCY_ENABLED": "true"}):
            result = route("hello", primary="", secondary="", generator=fake)
        self.assertEqual(result["model"], "llama3.2:3b")
        self.assertTrue(result["emergency_model"])
        self.assertEqual(result["response"], "real output from llama3.2:3b")


if __name__ == "__main__":
    unittest.main()
