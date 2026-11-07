import tempfile
import unittest
from pathlib import Path
from botany.garden import Garden
from botany.ai_records import add_ai_record, list_ai_records


class BotanyAITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.garden = Garden(Path(self.tmp.name) / "garden.sqlite3")
        self.crop = self.garden.plant("Ship 1", "Hydroponics", "Basil")

    def tearDown(self):
        self.garden.close()
        self.tmp.cleanup()

    def test_ai_record_is_unverified(self):
        rid = add_ai_record(self.garden.db, crop_id=self.crop, agent="Aria",
                            source_type="image_analysis", source_ref="image:sha256:example",
                            summary="Possible leaf discoloration", confidence=0.65)
        rows = list_ai_records(self.garden.db, self.crop)
        self.assertEqual(rows[0]["id"], rid)
        self.assertEqual(rows[0]["verification"], "unverified")

    def test_requires_provenance(self):
        with self.assertRaises(ValueError):
            add_ai_record(self.garden.db, crop_id=self.crop, agent="Alex",
                          source_type="ai_inference", source_ref="",
                          summary="Unknown", confidence=0.5)

    def test_rejects_unknown_agent(self):
        with self.assertRaises(ValueError):
            add_ai_record(self.garden.db, crop_id=self.crop, agent="anonymous",
                          source_type="simulation", source_ref="sim:1",
                          summary="Growth projection", confidence=0.7)


if __name__ == "__main__":
    unittest.main()
