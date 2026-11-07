import tempfile
import unittest
from pathlib import Path
from fleet_apps.solar_positions import FleetPositions


class PositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.positions = FleetPositions(Path(self.tmp.name) / "positions.db")

    def tearDown(self):
        self.positions.close()
        self.tmp.cleanup()

    def report(self, timestamp, source="simulation"):
        return self.positions.report(
            ship_id="Aurora", agent="Aria", source=source, source_ref="test:1",
            observed_at=timestamp, x_au=1, y_au=0.2, z_au=0)

    def test_latest_ignores_late_old_report(self):
        self.report("2026-11-07T15:00:00Z")
        self.report("2026-11-06T15:00:00Z")
        self.assertEqual(self.positions.latest()[0]["observed_at"], "2026-11-07T15:00:00+00:00")
        self.assertEqual(len(self.positions.history("Aurora")), 2)

    def test_rejects_unverified_source_label(self):
        with self.assertRaises(ValueError):
            self.report("2026-11-07T15:00:00Z", "real_for_sure")

    def test_rejects_invalid_coordinate(self):
        with self.assertRaises(ValueError):
            self.positions.report(ship_id="Aurora", agent="Alex", source="ai_estimate",
                                  source_ref="model:1", observed_at="2026-11-07T15:00:00Z",
                                  x_au=float("nan"), y_au=0, z_au=0)


if __name__ == "__main__":
    unittest.main()
