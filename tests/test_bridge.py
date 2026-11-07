import os
import unittest
from unittest.mock import patch
from bridge.server import Handler


class BridgeTests(unittest.TestCase):
    def test_bridge_has_expected_routes(self):
        self.assertTrue(callable(Handler.do_GET))
        self.assertTrue(callable(Handler.do_POST))

    def test_token_required(self):
        handler = object.__new__(Handler)
        handler.headers = {"Authorization": "Bearer wrong"}
        with patch.dict(os.environ, {"MONOLITH_BRIDGE_TOKEN": "a" * 40}):
            self.assertFalse(handler.authenticated())

    def test_token_matches(self):
        handler = object.__new__(Handler)
        handler.headers = {"Authorization": "Bearer " + "a" * 40}
        with patch.dict(os.environ, {"MONOLITH_BRIDGE_TOKEN": "a" * 40}):
            self.assertTrue(handler.authenticated())

    def test_short_token_never_accepted(self):
        handler = object.__new__(Handler)
        handler.headers = {"Authorization": "Bearer short"}
        with patch.dict(os.environ, {"MONOLITH_BRIDGE_TOKEN": "short"}):
            self.assertFalse(handler.authenticated())


if __name__ == "__main__":
    unittest.main()
