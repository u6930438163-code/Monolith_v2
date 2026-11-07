import unittest
from core.llm_router_v2 import route, ModelUnavailable


class LLMRouterTests(unittest.TestCase):
    def test_emergency_disabled_by_default(self):
        calls = []
        def mock(endpoint, model, prompt, timeout):
            calls.append(model)
            raise OSError("offline")
        with self.assertRaises(ModelUnavailable):
            route("hello", primary="primary", secondary="", emergency_enabled=False, generator=mock)
        self.assertEqual(calls, ["primary"])

    def test_emergency_3b_when_enabled(self):
        calls = []
        def mock(endpoint, model, prompt, timeout):
            calls.append(model)
            if model == "primary":
                raise OSError("offline")
            return "ok"
        result = route("hello", primary="primary", secondary="", emergency_enabled=True, generator=mock)
        self.assertEqual(calls, ["primary", "llama3.2:3b"])
        self.assertTrue(result["emergency_model"])


if __name__ == "__main__":
    unittest.main()
