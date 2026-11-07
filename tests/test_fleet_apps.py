import tempfile
import unittest
from pathlib import Path
from fleet_apps.registry import Shipyard


class ShipyardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.shipyard = Shipyard(Path(self.tmp.name) / "fleet.sqlite3")

    def tearDown(self):
        self.shipyard.close()
        self.tmp.cleanup()

    def test_create_and_delegate(self):
        app = self.shipyard.create_app("botany-fleet", "Botanika", "Cała flota", "Uprawy na statkach")
        task = self.shipyard.task(app, "Create dashboard", "Codex", "owner")
        self.assertEqual(len(self.shipyard.tasks(app)), 1)
        self.assertEqual(self.shipyard.tasks(app)[0]["id"], task)
        self.assertEqual(self.shipyard.apps()[0]["status"], "queued")

    def test_reject_bad_slug(self):
        with self.assertRaises(ValueError):
            self.shipyard.create_app("../bad", "Bad", "Ship", "Description")

    def test_unknown_agent(self):
        app = self.shipyard.create_app("ship-panel", "Panel", "Ship", "Description")
        with self.assertRaises(ValueError):
            self.shipyard.task(app, "Task", "Unknown", "owner")


if __name__ == "__main__":
    unittest.main()
