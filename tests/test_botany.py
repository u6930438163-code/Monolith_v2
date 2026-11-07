import tempfile
import unittest
from pathlib import Path
from botany.garden import Garden


class BotanyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.garden = Garden(Path(self.temp.name) / "garden.sqlite3")

    def tearDown(self):
        self.garden.close()
        self.temp.cleanup()

    def test_crop_lifecycle(self):
        cid = self.garden.plant("Vessel 1", "Hydroponics A", "Ocimum basilicum")
        self.garden.change_stage(cid, "seedling")
        self.assertEqual(self.garden.crops()[0]["stage"], "seedling")

    def test_observation_requires_source(self):
        cid = self.garden.plant("Vessel 1", "A", "Lettuce")
        with self.assertRaises(ValueError):
            self.garden.observe(cid, source_mode="verified_by_ai", ph=6)
        self.garden.observe(cid, source_mode="manual_observation", ph=6)

    def test_research_only(self):
        cid = self.garden.plant("Vessel 1", "A", "Mint")
        bid = self.garden.research_batch(cid, "Exploratory sample")
        status = self.garden.db.execute("SELECT status FROM research_batches WHERE id=?", (bid,)).fetchone()[0]
        self.assertEqual(status, "research_only")

    def test_invalid_stage(self):
        cid = self.garden.plant("Vessel 1", "A", "Mint")
        with self.assertRaises(ValueError):
            self.garden.change_stage(cid, "miracle_growth")


if __name__ == "__main__":
    unittest.main()
