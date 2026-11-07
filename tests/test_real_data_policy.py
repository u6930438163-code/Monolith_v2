import unittest
from datetime import datetime, timedelta, timezone
from core.real_data_policy import validate_observation, display_status


class RealDataPolicyTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "source": "authenticated_sensor",
            "source_ref": "sensor://fleet/receiver-01",
            "observed_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            "authenticated": True,
        }

    def test_real_authenticated_measurement(self):
        self.assertTrue(validate_observation(self.base))

    def test_simulation_rejected(self):
        with self.assertRaises(ValueError):
            validate_observation({**self.base, "source": "simulation"})

    def test_ai_estimate_rejected(self):
        with self.assertRaises(ValueError):
            validate_observation({**self.base, "source": "ai_estimate"})

    def test_unverified_sensor_rejected(self):
        with self.assertRaises(ValueError):
            validate_observation({**self.base, "authenticated": False})

    def test_no_data(self):
        self.assertEqual(display_status(None), "Brak danych")


if __name__ == "__main__":
    unittest.main()
