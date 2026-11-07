import os
import unittest
from unittest.mock import patch
from core.llm_control import status


class LLMControlTests(unittest.TestCase):
    def test_off_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            result = status()
        self.assertFalse(result["enabled"])
        self.assertEqual(result["model"], "llama3.2:3b")
        self.assertIsNone(result["installed"])

    def test_explicit_enable(self):
        with patch.dict(os.environ, {"MONOLITH_LLM_EMERGENCY_ENABLED": "true"}):
            self.assertTrue(status()["enabled"])


if __name__ == "__main__":
    unittest.main()
