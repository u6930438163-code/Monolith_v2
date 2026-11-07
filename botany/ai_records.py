"""AI-generated botany notes with provenance and explicit verification status."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone

AGENTS = frozenset({"Aria", "Alex", "Astyria", "Aurelius"})
SOURCES = frozenset({"image_analysis", "sensor_reading", "ai_inference", "simulation"})
STATUS = frozenset({"unverified", "verified", "rejected"})


def init(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ai_botany_records (
        id TEXT PRIMARY KEY, crop_id TEXT NOT NULL REFERENCES crops(id),
        agent TEXT NOT NULL, source_type TEXT NOT NULL, source_ref TEXT NOT NULL,
        summary TEXT NOT NULL, confidence REAL NOT NULL,
        verification TEXT NOT NULL DEFAULT 'unverified',
        created_at TEXT NOT NULL)""")
    db.commit()


def add_ai_record(db, *, crop_id, agent, source_type, source_ref, summary, confidence):
    init(db)
    if agent not in AGENTS or source_type not in SOURCES:
        raise ValueError("Invalid agent or source")
    if not isinstance(source_ref, str) or not 0 < len(source_ref) <= 512:
        raise ValueError("Source reference required")
    if not isinstance(summary, str) or not 0 < len(summary.strip()) <= 3000:
        raise ValueError("Invalid summary")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError("Invalid confidence")
    if db.execute("SELECT 1 FROM crops WHERE id=?", (crop_id,)).fetchone() is None:
        raise KeyError("Crop not found")
    record_id = uuid.uuid4().hex
    with db:
        db.execute("INSERT INTO ai_botany_records VALUES (?,?,?,?,?,?,?,?,?)",
                   (record_id, crop_id, agent, source_type, source_ref, summary,
                    float(confidence), "unverified", datetime.now(timezone.utc).isoformat()))
    return record_id


def list_ai_records(db, crop_id):
    init(db)
    return [dict(row) for row in db.execute(
        "SELECT * FROM ai_botany_records WHERE crop_id=? ORDER BY created_at DESC", (crop_id,))]


def main():
    import argparse
    from botany.garden import Garden
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="botany.sqlite3")
    sub = p.add_subparsers(dest="action", required=True)
    add = sub.add_parser("add")
    add.add_argument("crop_id")
    add.add_argument("agent", choices=sorted(AGENTS))
    add.add_argument("source_type", choices=sorted(SOURCES))
    add.add_argument("source_ref")
    add.add_argument("summary")
    add.add_argument("--confidence", type=float, required=True)
    ls = sub.add_parser("list")
    ls.add_argument("crop_id")
    args = p.parse_args()
    garden = Garden(args.db)
    try:
        if args.action == "add":
            print(json.dumps({"record_id": add_ai_record(
                garden.db, crop_id=args.crop_id, agent=args.agent,
                source_type=args.source_type, source_ref=args.source_ref,
                summary=args.summary, confidence=args.confidence)}))
        else:
            print(json.dumps(list_ai_records(garden.db, args.crop_id), ensure_ascii=False, indent=2))
    finally:
        garden.close()


if __name__ == "__main__":
    main()
