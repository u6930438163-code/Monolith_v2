import tempfile
import unittest
from pathlib import Path
from codex import worker
from codex.mcp_server import process


def call(name, args):
    return {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args}}


class MCPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = worker.DB
        worker.DB = Path(self.temp.name) / "jobs.sqlite3"

    def tearDown(self):
        worker.DB = self.old_db
        self.temp.cleanup()

    def test_tools_list(self):
        r = process({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual(len(r["result"]["tools"]), 2)

    def test_unauthorized(self):
        r = process(call("codex_enqueue", {"prompt": "check"}))
        self.assertEqual(r["error"]["code"], -32001)

    def test_enqueue_and_status(self):
        r = process(call("codex_enqueue", {"prompt": "check"}), actor="Aria", authorized=True)
        import json
        job_id = json.loads(r["result"]["content"][0]["text"])["job_id"]
        s = process(call("codex_status", {"job_id": job_id}), actor="Aria", authorized=True)
        self.assertEqual(json.loads(s["result"]["content"][0]["text"])["status"], "queued")
        denied = process(call("codex_status", {"job_id": job_id}), actor="Alex", authorized=True)
        self.assertTrue(denied["result"]["isError"])

    def test_actor_spoofing_rejected(self):
        r = process(call("codex_enqueue", {"prompt": "check", "actor": "owner"}),
                    actor="Aria", authorized=True)
        self.assertTrue(r["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
