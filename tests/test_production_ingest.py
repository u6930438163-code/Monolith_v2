import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from core.production_ingest import ProductionFleetIngest


class ProductionIngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ingest = ProductionFleetIngest(Path(self.tmp.name) / "fleet.db",
                                            trusted_adapters={"receiver-01": "local-test-token"})
        self.record = dict(adapter_id="receiver-01", adapter_token="local-test-token",
                           ship_id="Aurora", observed_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
                           x_au=1.0, y_au=0.0, z_au=0.0)

    def tearDown(self):
        self.ingest.close()
        self.tmp.cleanup()

    def test_trusted_record_visible(self):
        self.ingest.ingest_position(**self.record)
        self.assertEqual(self.ingest.latest()[0]["ship_id"], "Aurora")

    def test_untrusted_adapter_denied(self):
        with self.assertRaises(PermissionError):
            self.ingest.ingest_position(**{**self.record, "adapter_token": "wrong"})

    def test_no_data_is_empty(self):
        self.assertEqual(self.ingest.latest(), [])

    def test_future_data_denied(self):
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):
            self.ingest.ingest_position(**{**self.record, "observed_at": future})


if __name__ == "__main__":
    unittest.main()
