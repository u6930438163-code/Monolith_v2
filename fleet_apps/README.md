# Stocznia Aplikacji Floty — Fleet App Shipyard

Backend MVP for apps requested through the Monolith chat. This is a durable SQLite registry of projects and tasks, not yet a LibreChat tool or autonomous code execution service.

Capabilities:
- Create named applications for a vessel, station, or the whole fleet.
- Queue development requests for Aria, Alex, Astyria, Aurelius or Codex.
- Track app/task IDs and status in SQLite.
- No automatic deployment; statuses are initial bookkeeping only.

Quick start from repository root:
```bash
python3 -m fleet_apps.registry --db fleet.sqlite3 create botany-fleet "Botanika Floty" "Cała flota" "Panel upraw i badań"
python3 -m fleet_apps.registry --db fleet.sqlite3 list
python3 -m unittest tests.test_fleet_apps -v
```

Next integrations: authenticated LibreChat tool adapter; permission engine; secure delegation to the existing Codex job queue; sandboxed builds and tests; per-app secrets and storage; GitHub repository mapping; artifact signing and deployment with rollback; live event notifications. Chat messages must never be accepted as authenticated actor identities without verification.

Security: the registry does not execute code, run shell commands, or grant root. Application builds must run isolated from the Monolith host. Untrusted apps cannot access ship telemetry or actuators without separately granted permissions.
