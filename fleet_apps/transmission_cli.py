"""Terminal entry point for creating and listing fleet transmission investigations."""
import argparse
import json
from fleet_apps.transmissions import TransmissionInvestigations


def main():
    parser = argparse.ArgumentParser(description="Monolith fleet transmission investigations")
    parser.add_argument("--db", default="transmissions.sqlite3")
    sub = parser.add_subparsers(dest="action", required=True)
    request = sub.add_parser("request")
    request.add_argument("contact_id")
    request.add_argument("--agent", required=True, choices=["Aria", "Alex", "Astyria", "Aurelius"])
    request.add_argument("--kind", required=True, choices=["radio", "network", "hyperspace_simulation", "unknown"])
    request.add_argument("--source-ref", required=True)
    request.add_argument("--requested-by", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("contact_id")
    args = parser.parse_args()
    registry = TransmissionInvestigations(args.db)
    try:
        if args.action == "request":
            result = {"investigation_id": registry.request(
                args.contact_id, requested_by=args.requested_by,
                assigned_agent=args.agent, signal_kind=args.kind, source_ref=args.source_ref)}
        else:
            result = registry.list_for_contact(args.contact_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        registry.close()


if __name__ == "__main__":
    main()
