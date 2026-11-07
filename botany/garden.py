"""Space botany registry: persistent crop lifecycle, observations and research batches.

No medical efficacy claims and no autonomous drug manufacturing controls.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

STAGES = ("seed", "seedling", "vegetative", "flowering", "harvested", "archived")
MODES = ("simulated", "sensor_verified", "manual_observation")


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class Garden:
    def __init__(self, path):
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS crops (
          id TEXT PRIMARY KEY, vessel TEXT NOT NULL, habitat TEXT NOT NULL,
          species TEXT NOT NULL, stage TEXT NOT NULL, source_mode TEXT NOT NULL,
          planted_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS observations (
          id TEXT PRIMARY KEY, crop_id TEXT NOT NULL REFERENCES crops(id),
          timestamp TEXT NOT NULL, source_mode TEXT NOT NULL,
          temperature_c REAL, humidity_percent REAL, light_lux REAL,
          ph REAL, notes TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS research_batches (
          id TEXT PRIMARY KEY, crop_id TEXT NOT NULL REFERENCES crops(id),
          created_at TEXT NOT NULL, description TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('research_only','under_review','rejected')),
          safety_notes TEXT NOT NULL);
        """)
        self.db.execute("PRAGMA foreign_keys=ON")

    def plant(self, vessel, habitat, species, *, source_mode="manual_observation"):
        if source_mode not in MODES or not all(isinstance(v, str) and 0 < len(v.strip()) <= 120 for v in (vessel, habitat, species)):
            raise ValueError("Invalid plant record")
        crop_id = uuid.uuid4().hex
        now = utcnow()
        with self.db:
            self.db.execute("INSERT INTO crops VALUES (?,?,?,?,?,?,?,?)",
                            (crop_id, vessel, habitat, species, "seed", source_mode, now, now))
        return crop_id

    def change_stage(self, crop_id, stage):
        if stage not in STAGES:
            raise ValueError("Invalid stage")
        with self.db:
            result = self.db.execute("UPDATE crops SET stage=?,updated_at=? WHERE id=?",
                                     (stage, utcnow(), crop_id))
        if result.rowcount != 1:
            raise KeyError("Crop not found")

    def observe(self, crop_id, *, source_mode, temperature_c=None, humidity_percent=None,
                light_lux=None, ph=None, notes=""):
        if source_mode not in MODES:
            raise ValueError("Invalid source mode")
        for value, low, high in ((temperature_c, -80, 100), (humidity_percent, 0, 100),
                                 (light_lux, 0, 250000), (ph, 0, 14)):
            if value is not None and (not isinstance(value, (int, float)) or not low <= value <= high):
                raise ValueError("Measurement out of bounds")
        if not isinstance(notes, str) or len(notes) > 2000:
            raise ValueError("Invalid notes")
        oid = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?)",
                            (oid, crop_id, utcnow(), source_mode, temperature_c,
                             humidity_percent, light_lux, ph, notes))
        return oid

    def research_batch(self, crop_id, description, safety_notes=""):
        if not isinstance(description, str) or not 0 < len(description.strip()) <= 2000:
            raise ValueError("Invalid description")
        if not isinstance(safety_notes, str) or len(safety_notes) > 2000:
            raise ValueError("Invalid safety notes")
        bid = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO research_batches VALUES (?,?,?,?,?,?)",
                            (bid, crop_id, utcnow(), description, "research_only", safety_notes))
        return bid

    def crops(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM crops ORDER BY planted_at DESC")]

    def close(self):
        self.db.close()


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="botany.sqlite3")
    sub = p.add_subparsers(dest="action", required=True)
    plant = sub.add_parser("plant")
    plant.add_argument("vessel")
    plant.add_argument("habitat")
    plant.add_argument("species")
    sub.add_parser("list")
    args = p.parse_args()
    garden = Garden(args.db)
    try:
        if args.action == "plant":
            print(json.dumps({"crop_id": garden.plant(args.vessel, args.habitat, args.species)}))
        else:
            print(json.dumps(garden.crops(), ensure_ascii=False, indent=2))
    finally:
        garden.close()


if __name__ == "__main__":
    main()
