import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from mvp.status_server import snapshot


class MVPStatusTests(unittest.TestCase):
    def test_missing_databases_return_no_fabricated_positions(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.dict("os.environ", {
                "MONOLITH_POSITIONS_DB": str(Path(d) / "missing-positions.db"),
                "MONOLITH_TRANSMISSIONS_DB": str(Path(d) / "missing-transmissions.db"),
            }):
                result = snapshot()
        self.assertEqual(result["mode"], "real_data_only")
        self.assertEqual(result["fleet_positions"], [])
        self.assertEqual(result["transmission_investigations"], [])
        self.assertEqual(result["agent_status"]["Aria"], "not_connected")


if __name__ == "__main__":
    unittest.main()
