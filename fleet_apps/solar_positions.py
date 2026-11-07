"""Fleet position reports with provenance, history and timestamp ordering.

This module stores supplied positions; it does not infer live telemetry.
"""
import math
import sqlite3
import uuid
from datetime import datetime, timezone

AGENTS = frozenset(("Aria", "Alex", "Astyria", "Aurelius"))
SOURCES = frozenset(("telemetry", "ai_estimate", "simulation"))
FRAME = "heliocentric_ecliptic_J2000"


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be ISO-8601 UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("timestamp must be UTC")
    return parsed.astimezone(timezone.utc).isoformat()


class FleetPositions:
    def __init__(self, path):
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS position_reports (
            id TEXT PRIMARY KEY, ship_id TEXT NOT NULL, agent TEXT NOT NULL,
            source TEXT NOT NULL, source_ref TEXT NOT NULL,
            observed_at TEXT NOT NULL, received_at TEXT NOT NULL,
            coordinate_frame TEXT NOT NULL,
            x_au REAL NOT NULL, y_au REAL NOT NULL, z_au REAL NOT NULL,
            mission TEXT NOT NULL, status TEXT NOT NULL)""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_ship_time ON position_reports(ship_id,observed_at)")
        self.db.commit()

    def report(self, *, ship_id, agent, source, source_ref, observed_at,
               x_au, y_au, z_au, mission="", status="unknown"):
        if agent not in AGENTS or source not in SOURCES:
            raise ValueError("unknown agent or source")
        for value, limit in ((ship_id, 120), (source_ref, 512), (mission, 500), (status, 120)):
            if not isinstance(value, str) or len(value) > limit:
                raise ValueError("invalid string")
        if not ship_id.strip() or not source_ref.strip():
            raise ValueError("ship and provenance required")
        coords = (x_au, y_au, z_au)
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 10000 for v in coords):
            raise ValueError("invalid coordinates")
        stamp = parse_time(observed_at)
        rid = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO position_reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (rid, ship_id, agent, source, source_ref, stamp,
                             datetime.now(timezone.utc).isoformat(), FRAME,
                             *map(float, coords), mission, status))
        return rid

    def latest(self):
        rows = self.db.execute("""SELECT * FROM position_reports p WHERE
            NOT EXISTS (SELECT 1 FROM position_reports newer WHERE
            newer.ship_id=p.ship_id AND
            (newer.observed_at>p.observed_at OR
             (newer.observed_at=p.observed_at AND newer.received_at>p.received_at)))
            ORDER BY ship_id""").fetchall()
        return [dict(r) for r in rows]

    def history(self, ship_id, limit=100):
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("invalid limit")
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM position_reports WHERE ship_id=? ORDER BY observed_at DESC, received_at DESC LIMIT ?",
            (ship_id, limit))]

    def close(self):
        self.db.close()
