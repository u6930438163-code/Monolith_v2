"""Multi-vessel detection registry with conservative identity handling.

Sensor observations are reports, never proof of alliance or identity.
"""
import math
import sqlite3
import uuid
from datetime import datetime, timezone

CLASSIFICATIONS = frozenset({"unknown", "potential_ally", "confirmed_ally", "own"})
SOURCES = frozenset({"sensor", "authenticated_peer", "manual", "simulation"})


class Contacts:
    def __init__(self, path):
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
            classification TEXT NOT NULL DEFAULT 'unknown',
            identity_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS detections (
            id TEXT PRIMARY KEY, contact_id TEXT NOT NULL REFERENCES contacts(id),
            observer_ship TEXT NOT NULL, source TEXT NOT NULL, source_ref TEXT NOT NULL,
            observed_at TEXT NOT NULL, x_au REAL NOT NULL, y_au REAL NOT NULL,
            z_au REAL NOT NULL, confidence REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_contact_observations
            ON detections(contact_id, observed_at);
        """)
        self.db.execute("PRAGMA foreign_keys=ON")

    def create_contact(self, display_name):
        if not isinstance(display_name, str) or not 0 < len(display_name.strip()) <= 120:
            raise ValueError("Invalid contact name")
        cid = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO contacts VALUES (?,?,?,?,?)",
                            (cid, display_name, "unknown", 0, datetime.now(timezone.utc).isoformat()))
        return cid

    def detect(self, contact_id, *, observer_ship, source, source_ref, observed_at,
               x_au, y_au, z_au, confidence):
        if source not in SOURCES:
            raise ValueError("Invalid detection source")
        if not all(isinstance(s, str) and 0 < len(s.strip()) <= 512
                   for s in (observer_ship, source_ref)):
            raise ValueError("Observer and source reference required")
        try:
            stamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise ValueError("Invalid timestamp") from exc
        if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError("UTC timestamp required")
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 10000
               for v in (x_au, y_au, z_au)):
            raise ValueError("Invalid coordinates")
        if not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Invalid confidence")
        if not self.db.execute("SELECT 1 FROM contacts WHERE id=?", (contact_id,)).fetchone():
            raise KeyError("Contact not found")
        did = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO detections VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (did, contact_id, observer_ship, source, source_ref,
                             stamp.astimezone(timezone.utc).isoformat(),
                             float(x_au), float(y_au), float(z_au), float(confidence)))
        return did

    def contacts(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM contacts ORDER BY created_at DESC")]

    def observations(self, contact_id):
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM detections WHERE contact_id=? ORDER BY observed_at DESC", (contact_id,))]

    def close(self):
        self.db.close()
