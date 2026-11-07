"""Server-side permission checks for Monolith_v2 (standard library only).

This module is a starting policy engine, not an authentication provider.
Callers MUST derive actor identity from verified authentication, never from
untrusted request payloads.
"""
from dataclasses import dataclass, field

RESOURCES = frozenset({
    "chat", "agents", "workers", "terminal", "diagnostics", "remote_desktop",
    "ollama", "models", "vision", "github", "missions", "infrastructure",
    "communications", "attachments", "explorer", "knowledge", "budget",
    "database", "ui", "deployment", "permissions", "development", "secrets",
})
ACTIONS = frozenset({"read", "execute", "change", "deploy", "manage"})
SENSITIVE = frozenset({"permissions", "secrets", "budget", "deployment", "remote_desktop", "terminal"})
AGENTS = frozenset({"Aria", "Alex", "Astyria", "Aurelius"})


@dataclass
class PermissionEngine:
    owner: str
    grants: dict[str, set[tuple[str, str]]] = field(default_factory=dict)
    denies: dict[str, set[tuple[str, str]]] = field(default_factory=dict)

    def grant(self, actor: str, resource: str, action: str, *, approved_by: str) -> None:
        self._validate(resource, action)
        if approved_by != self.owner:
            raise PermissionError("Only owner can grant access")
        self.grants.setdefault(actor, set()).add((resource, action))

    def revoke(self, actor: str, resource: str, action: str, *, approved_by: str) -> None:
        self._validate(resource, action)
        if approved_by != self.owner:
            raise PermissionError("Only owner can revoke access")
        self.grants.setdefault(actor, set()).discard((resource, action))

    def deny(self, actor: str, resource: str, action: str, *, approved_by: str) -> None:
        self._validate(resource, action)
        if approved_by != self.owner:
            raise PermissionError("Only owner can deny access")
        self.denies.setdefault(actor, set()).add((resource, action))

    def allowed(self, actor: str, resource: str, action: str, *, owner_approved: bool = False) -> bool:
        self._validate(resource, action)
        if actor == self.owner:
            return True
        if (resource, action) in self.denies.get(actor, set()):
            return False
        if (resource, action) not in self.grants.get(actor, set()):
            return False
        if resource in SENSITIVE and action != "read" and not owner_approved:
            return False
        return True

    @staticmethod
    def _validate(resource: str, action: str) -> None:
        if resource not in RESOURCES or action not in ACTIONS:
            raise ValueError("Unknown resource or action")
