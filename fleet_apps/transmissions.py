"""Transmission investigation registry for fleet contacts.

Stores metadata and requests only. No interception, decoding or RF hardware control.
"""
import sqlite3
import uuid
from datetime import datetime, timezone

KINDS = frozenset({"radio", "network", "hyperspace_simulation", "unknown"})
STATES = frozenset({"queued", "analyzing", "completed", "failed"})


class TransmissionInvestigations:
    def __init__(self, db_path):
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY, contact_id TEXT NOT NULL,
            requested_by TEXT NOT NULL, assigned_agent TEXT NOT NULL,
            signal_kind TEXT NOT NULL, source_ref TEXT NOT NULL,
            status TEXT NOT NULL, summary TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        self.db.commit()

    def request(self, contact_id, *, requested_by, assigned_agent, signal_kind, source_ref):
        if assigned_agent not in ("Aria", "Alex", "Astyria", "Aurelius"):
            raise ValueError("Unknown agent")
        if signal_kind not in KINDS:
            raise ValueError("Unknown signal type")
        if not all(isinstance(v, str) and 0 < len(v.strip()) <= 512
                   for v in (contact_id, requested_by, source_ref)):
            raise ValueError("Contact, requester and signal source are required")
        now = datetime.now(timezone.utc).isoformat()
        iid = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO investigations VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (iid, contact_id, requested_by, assigned_agent, signal_kind,
                             source_ref, "queued", "", now, now))
        return iid

    def list_for_contact(self, contact_id):
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM investigations WHERE contact_id=? ORDER BY created_at DESC",
            (contact_id,))]

    def close(self):
        self.db.close()
