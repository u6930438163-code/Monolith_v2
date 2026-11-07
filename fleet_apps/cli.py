"""Terminal interface for fleet position registry.

Run: python3 -m fleet_apps.cli --db fleet-positions.sqlite3 list
"""
import argparse
import json
from fleet_apps.solar_positions import FleetPositions


def main():
    p = argparse.ArgumentParser(prog="monolith fleet")
    p.add_argument("--db", default="fleet-positions.sqlite3")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    history = sub.add_parser("history")
    history.add_argument("ship")
    status = sub.add_parser("status")
    status.add_argument("ship")
    report = sub.add_parser("report")
    report.add_argument("ship")
    report.add_argument("--agent", required=True, choices=["Aria", "Alex", "Astyria", "Aurelius"])
    report.add_argument("--source", required=True, choices=["telemetry", "ai_estimate", "simulation"])
    report.add_argument("--source-ref", required=True)
    report.add_argument("--observed-at", required=True)
    report.add_argument("--x-au", type=float, required=True)
    report.add_argument("--y-au", type=float, required=True)
    report.add_argument("--z-au", type=float, required=True)
    report.add_argument("--mission", default="")
    report.add_argument("--status", default="unknown")
    args = p.parse_args()
    positions = FleetPositions(args.db)
    try:
        if args.command == "list":
            result = positions.latest()
        elif args.command == "history":
            result = positions.history(args.ship)
        elif args.command == "status":
            result = next((r for r in positions.latest() if r["ship_id"] == args.ship), None)
            if result is None:
                p.error("Ship has no position reports")
        else:
            result = {"report_id": positions.report(
                ship_id=args.ship, agent=args.agent, source=args.source,
                source_ref=args.source_ref, observed_at=args.observed_at,
                x_au=args.x_au, y_au=args.y_au, z_au=args.z_au,
                mission=args.mission, status=args.status)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        positions.close()


if __name__ == "__main__":
    main()
