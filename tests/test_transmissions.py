import tempfile
import unittest
from pathlib import Path
from fleet_apps.transmissions import TransmissionInvestigations


class TransmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.registry = TransmissionInvestigations(Path(self.temp.name) / "transmissions.db")

    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()

    def test_queue_and_list(self):
        task = self.registry.request(
            "contact-01", requested_by="owner", assigned_agent="Astyria",
            signal_kind="hyperspace_simulation", source_ref="demo://contact-01")
        reports = self.registry.list_for_contact("contact-01")
        self.assertEqual(reports[0]["id"], task)
        self.assertEqual(reports[0]["status"], "queued")
        self.assertEqual(reports[0]["signal_kind"], "hyperspace_simulation")

    def test_rejects_missing_source(self):
        with self.assertRaises(ValueError):
            self.registry.request("contact-01", requested_by="owner",
                                  assigned_agent="Aria", signal_kind="radio", source_ref="")

    def test_rejects_unknown_agent(self):
        with self.assertRaises(ValueError):
            self.registry.request("contact-01", requested_by="owner",
                                  assigned_agent="unknown", signal_kind="network",
                                  source_ref="network://peer")


if __name__ == "__main__":
    unittest.main()
