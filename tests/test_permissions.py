import unittest
from core.permissions import PermissionEngine, RESOURCES, AGENTS


class PermissionsTest(unittest.TestCase):
    def setUp(self):
        self.engine = PermissionEngine(owner="owner")

    def test_default_deny_for_all_agents_and_resources(self):
        for agent in AGENTS:
            for resource in RESOURCES:
                self.assertFalse(self.engine.allowed(agent, resource, "read"))

    def test_owner_has_access(self):
        self.assertTrue(self.engine.allowed("owner", "permissions", "manage"))

    def test_grant_requires_owner(self):
        with self.assertRaises(PermissionError):
            self.engine.grant("Aria", "chat", "read", approved_by="Alex")

    def test_grant_revoke(self):
        self.engine.grant("Aria", "chat", "read", approved_by="owner")
        self.assertTrue(self.engine.allowed("Aria", "chat", "read"))
        self.engine.revoke("Aria", "chat", "read", approved_by="owner")
        self.assertFalse(self.engine.allowed("Aria", "chat", "read"))

    def test_sensitive_actions_require_approval(self):
        self.engine.grant("Astyria", "terminal", "execute", approved_by="owner")
        self.assertFalse(self.engine.allowed("Astyria", "terminal", "execute"))
        self.assertTrue(self.engine.allowed("Astyria", "terminal", "execute", owner_approved=True))

    def test_explicit_deny_overrides_grant(self):
        self.engine.grant("Alex", "github", "read", approved_by="owner")
        self.engine.deny("Alex", "github", "read", approved_by="owner")
        self.assertFalse(self.engine.allowed("Alex", "github", "read"))

    def test_unknown_resource_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.allowed("Alex", "other", "read")


if __name__ == "__main__":
    unittest.main()
