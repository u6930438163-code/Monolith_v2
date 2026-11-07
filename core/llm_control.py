"""Operator CLI for Monolith's opt-in emergency Llama 3.2 3B.

Does not modify host environment, download models or silently enable fallback.
"""
import argparse
import json
import os
import urllib.request
from core.llm_router_v2 import EMERGENCY_MODEL, route, ModelUnavailable


def status():
    enabled = os.environ.get("MONOLITH_LLM_EMERGENCY_ENABLED", "false").lower() in ("true", "1", "yes")
    return {"model": EMERGENCY_MODEL, "enabled": enabled, "mode": "third_tier_emergency",
            "installed": None, "connected": None,
            "note": "Model installation and Ollama connectivity not yet verified"}


def main():
    parser = argparse.ArgumentParser(description="Monolith LLM control")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status")
    ask = sub.add_parser("ask")
    ask.add_argument("prompt")
    args = parser.parse_args()
    if args.action == "status":
        result = status()
    else:
        try:
            result = route(args.prompt)
        except ModelUnavailable as exc:
            parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
