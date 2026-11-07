"""Fleet App Shipyard: persistent app projects and development requests.

No code execution, deployments, or privilege escalation in this registry.
"""
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone

AGENTS = frozenset({"Aria", "Alex", "Astyria", "Aurelius", "Codex"})
STATES = frozenset({"draft", "queued", "building", "testing", "ready", "deployed", "failed", "archived"})
SLUG = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


def now():
    return datetime.now(timezone.utc).isoformat()


class Shipyard:
    def __init__(self, db_path):
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS fleet_apps (
            id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL, vessel TEXT NOT NULL,
            description TEXT NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS app_tasks (
            id TEXT PRIMARY KEY, app_id TEXT NOT NULL REFERENCES fleet_apps(id),
            requested_by TEXT NOT NULL, assigned_to TEXT NOT NULL,
            instruction TEXT NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL)""")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.commit()

    def create_app(self, slug, name, vessel, description):
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            raise ValueError("Invalid application slug")
        if not all(isinstance(s, str) and 0 < len(s.strip()) <= limit
                   for s, limit in ((name, 120), (vessel, 120), (description, 4000))):
            raise ValueError("Invalid app details")
        app_id = uuid.uuid4().hex
        t = now()
        with self.db:
            self.db.execute("INSERT INTO fleet_apps VALUES (?,?,?,?,?,?,?,?)",
                            (app_id, slug, name, vessel, description, "draft", t, t))
        return app_id

    def task(self, app_id, instruction, assigned_to, requested_by):
        if assigned_to not in AGENTS:
            raise ValueError("Unknown agent")
        if not isinstance(requested_by, str) or not 0 < len(requested_by) <= 120:
            raise ValueError("Invalid requester")
        if not isinstance(instruction, str) or not 0 < len(instruction.strip()) <= 8000:
            raise ValueError("Invalid instruction")
        if not self.db.execute("SELECT 1 FROM fleet_apps WHERE id=?", (app_id,)).fetchone():
            raise KeyError("App not found")
        task_id = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO app_tasks VALUES (?,?,?,?,?,?,?)",
                            (task_id, app_id, requested_by, assigned_to, instruction, "queued", now()))
            self.db.execute("UPDATE fleet_apps SET status='queued',updated_at=? WHERE id=?", (now(), app_id))
        return task_id

    def apps(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM fleet_apps ORDER BY created_at DESC")]

    def tasks(self, app_id):
        return [dict(row) for row in self.db.execute(
            "SELECT * FROM app_tasks WHERE app_id=? ORDER BY created_at DESC", (app_id,))]

    def close(self):
        self.db.close()


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="fleet_apps.sqlite3")
    sub = p.add_subparsers(dest="action", required=True)
    create = sub.add_parser("create")
    create.add_argument("slug")
    create.add_argument("name")
    create.add_argument("vessel")
    create.add_argument("description")
    task = sub.add_parser("task")
    task.add_argument("app_id")
    task.add_argument("agent", choices=sorted(AGENTS))
    task.add_argument("instruction")
    sub.add_parser("list")
    args = p.parse_args()
    shipyard = Shipyard(args.db)
    try:
        if args.action == "create":
            result = {"app_id": shipyard.create_app(args.slug, args.name, args.vessel, args.description)}
        elif args.action == "task":
            result = {"task_id": shipyard.task(args.app_id, args.instruction, args.agent, "owner-cli")}
        else:
            result = shipyard.apps()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        shipyard.close()


if __name__ == "__main__":
    main()
