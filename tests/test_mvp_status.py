import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
from core.production_ingest import ProductionFleetIngest
from diagnostics.collector import _service_states
from fleet_apps.transmissions import TransmissionInvestigations
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
        self.assertEqual(result["agent_status"]["Aria"]["status"], "not_connected")

    def test_agent_status_reflects_endpoint_configuration(self):
        with patch.dict("os.environ", {
            "MONOLITH_AGENT_ARIA_URL": "https://aria.example.org/messages",
            "MONOLITH_AGENT_ARIA_TOKEN": "configured-secret",
        }, clear=True):
            result = snapshot()
        self.assertEqual(result["agent_status"]["Aria"]["status"], "not_verified")
        self.assertEqual(result["agent_status"]["Aria"]["configuration"], "configured")
        self.assertEqual(result["agent_status"]["Aria"]["source"], "host_environment")
        self.assertIsNotNone(result["agent_status"]["Aria"]["timestamp_utc"])
        self.assertEqual(result["agent_status"]["Alex"]["status"], "not_connected")

    def test_service_and_diagnostic_status_include_source_and_time(self):
        with patch.dict("os.environ", {}, clear=True):
            result = snapshot()
        self.assertIn(result["ollama"]["status"], {"not_connected", "connected", "no_data"})
        self.assertIsNotNone(result["ollama"]["timestamp_utc"])
        self.assertEqual(result["ollama"]["source"], "http://127.0.0.1:11434")
        self.assertEqual(result["librechat"]["status"], "not_connected")
        self.assertIsNone(result["librechat"]["data"])
        self.assertEqual(result["diagnostics"]["source"], "local_os")
        self.assertIsNotNone(result["diagnostics"]["timestamp_utc"])
        diagnostic_data = result["diagnostics"]["data"]
        self.assertIn("processes", diagnostic_data)
        self.assertIn("ollama", diagnostic_data["services"])
        self.assertIn("timestamp", diagnostic_data["services"]["ollama"])

    def test_invalid_probe_url_does_not_expose_credentials(self):
        from mvp.status_server import _service_status
        result = _service_status("http://user:password@127.0.0.1:11434/api/tags?token=secret")
        self.assertEqual(result["status"], "not_connected")
        self.assertEqual(result["source"], "http://127.0.0.1:11434")

    def test_only_authenticated_telemetry_is_exposed(self):
        with tempfile.TemporaryDirectory() as directory:
            positions_db = Path(directory) / "fleet.db"
            ingest = ProductionFleetIngest(positions_db, trusted_adapters={"receiver": "token"})
            observed_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
            ingest.ingest_position(adapter_id="receiver", adapter_token="token", ship_id="Aurora",
                                   observed_at=observed_at, x_au=1, y_au=0, z_au=0)
            ingest.positions.report(ship_id="Demo", agent="Aria", source="simulation", source_ref="demo://1",
                                    observed_at=observed_at, x_au=2, y_au=0, z_au=0)
            ingest.close()
            transmissions_db = Path(directory) / "transmissions.db"
            investigations = TransmissionInvestigations(transmissions_db)
            investigations.request("contact", requested_by="owner", assigned_agent="Alex",
                                   signal_kind="radio", source_ref="unverified://signal")
            investigations.close()
            with patch.dict("os.environ", {
                "MONOLITH_POSITIONS_DB": str(positions_db),
                "MONOLITH_TRANSMISSIONS_DB": str(transmissions_db),
            }, clear=True):
                result = snapshot()
        self.assertEqual([row["ship_id"] for row in result["fleet_positions"]], ["Aurora"])
        self.assertEqual(result["fleet_positions"][0]["source_ref"], "trusted-adapter:receiver")
        self.assertEqual(result["transmission_investigations"], [])

    def test_service_probe_discards_non_state_systemctl_output(self):
        with patch("diagnostics.collector.shutil.which", return_value="/usr/bin/systemctl"), \
             patch("diagnostics.collector.subprocess.run",
                   return_value=SimpleNamespace(stdout="systemd is not running", returncode=1)):
            result = _service_states()
        self.assertEqual(result["ollama"]["status"], "no_data")
        self.assertIsNone(result["ollama"]["state"])


if __name__ == "__main__":
    unittest.main()
