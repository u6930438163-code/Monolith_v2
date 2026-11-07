import os
import unittest
from unittest.mock import patch
from agents.connection import config, status, send


class AgentConnectionTests(unittest.TestCase):
    def test_unconfigured_agents_are_not_connected(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(status()["Aria"], "not_connected")

    def test_invalid_endpoint_is_reported_as_not_connected(self):
        with patch.dict(os.environ, {
            "MONOLITH_AGENT_ARIA_URL": "http://agents.example.org/aria",
            "MONOLITH_AGENT_ARIA_TOKEN": "secret",
        }, clear=True):
            self.assertEqual(status()["Aria"], "not_connected")

    def test_https_configured(self):
        with patch.dict(os.environ, {
            "MONOLITH_AGENT_ALEX_URL": "https://agents.example.org/alex",
            "MONOLITH_AGENT_ALEX_TOKEN": "secret",
        }, clear=True):
            self.assertEqual(config("Alex")["status"], "configured")

    def test_public_http_rejected(self):
        with patch.dict(os.environ, {
            "MONOLITH_AGENT_ARIA_URL": "http://agents.example.org/aria",
            "MONOLITH_AGENT_ARIA_TOKEN": "secret",
        }, clear=True):
            with self.assertRaises(ValueError):
                config("Aria")

    def test_unconfigured_send_fails(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConnectionError):
                send("Astyria", "Status?")


if __name__ == "__main__":
    unittest.main()
