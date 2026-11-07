import unittest
from core.llm_fallback import generate_with_fallback, AllModelsUnavailable


class FallbackTests(unittest.TestCase):
    def test_third_model_works_after_failures(self):
        calls = []
        def fake(endpoint, model, prompt, timeout):
            calls.append(model)
            if model != "qwen3:1.7b":
                raise OSError("offline")
            return "Awaryjna odpowiedź"
        result = generate_with_fallback("status", primary="llama3.2-vision:11b",
                                        secondary="qwen3:4b", emergency="qwen3:1.7b",
                                        generator=fake)
        self.assertEqual(calls, ["llama3.2-vision:11b", "qwen3:4b", "qwen3:1.7b"])
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["model"], "qwen3:1.7b")

    def test_no_invented_reply_on_failure(self):
        def fail(*args):
            raise TimeoutError("offline")
        with self.assertRaises(AllModelsUnavailable):
            generate_with_fallback("status", primary="", secondary="",
                                   emergency="qwen3:1.7b", generator=fail)

    def test_reject_empty_prompt(self):
        with self.assertRaises(ValueError):
            generate_with_fallback(" ")


if __name__ == "__main__":
    unittest.main()
