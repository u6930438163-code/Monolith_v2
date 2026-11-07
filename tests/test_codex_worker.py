import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from codex import worker


class CodexQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = worker.DB
        worker.DB = Path(self.tmp.name) / "jobs.sqlite3"

    def tearDown(self):
        worker.DB = self.old_db
        self.tmp.cleanup()

    def test_enqueue_and_status(self):
        job_id = worker.enqueue("Aria", "Check diagnostics")
        item = worker.status(job_id)
        self.assertEqual(item["status"], "queued")
        self.assertEqual(item["actor"], "Aria")

    def test_reject_empty_prompt(self):
        with self.assertRaises(ValueError):
            worker.enqueue("Alex", " ")

    @patch("codex.worker.shutil.which", return_value=None)
    def test_missing_codex_cli_fails_job(self, _):
        job_id = worker.enqueue("owner", "Inspect tests")
        self.assertTrue(worker.run_next())
        self.assertEqual(worker.status(job_id)["status"], "failed")
        self.assertEqual(worker.status(job_id)["exit_code"], 127)

    def test_empty_queue(self):
        self.assertFalse(worker.run_next())


if __name__ == "__main__":
    unittest.main()
