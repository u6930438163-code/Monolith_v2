import unittest
from unittest.mock import patch
from control.ubuntu import execute


class UbuntuControlTests(unittest.TestCase):
    def test_disallows_arbitrary_service(self):
        with self.assertRaises(ValueError):
            execute("restart", "ssh", actor="alex")

    def test_disallows_arbitrary_action(self):
        with self.assertRaises(ValueError):
            execute("run", "ollama", actor="alex")

    @patch("control.ubuntu.subprocess.run")
    def test_read_only_status(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = "active\n"
        run.return_value.stderr = ""
        result = execute("status", "ollama", actor="aria")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(run.call_args.args[0], ["/usr/bin/systemctl", "is-active", "ollama.service"])

    @patch("control.ubuntu.subprocess.run")
    def test_restart_is_narrow_sudo(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = ""
        run.return_value.stderr = ""
        execute("restart", "monolith-bridge", actor="alex")
        self.assertEqual(run.call_args.args[0], ["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "restart", "monolith-bridge.service"])


if __name__ == "__main__":
    unittest.main()
