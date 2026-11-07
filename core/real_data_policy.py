"""Monolith operational real-data gate.

This module refuses simulated, synthetic, fabricated and source-less observations.
An AI inference is not a measurement; keep it separately labeled.
"""
from datetime import datetime, timezone

REAL_SOURCES = frozenset({"authenticated_sensor", "authenticated_telemetry", "verified_import", "operator_observation"})
REJECTED_SOURCES = frozenset({"simulation", "hyperspace_simulation", "synthetic", "demo", "ai_estimate", "ai_inference"})


def validate_observation(record):
    if not isinstance(record, dict):
        raise ValueError("Observation must be an object")
    source = record.get("source")
    if source not in REAL_SOURCES:
        raise ValueError("Operational data requires a real source; simulated and inferred data are rejected")
    reference = record.get("source_ref")
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError("Source reference required")
    observed_at = record.get("observed_at")
    if not isinstance(observed_at, str):
        raise ValueError("UTC observation timestamp required")
    try:
        timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid observation timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0:
        raise ValueError("Observation timestamp must be UTC")
    if timestamp > datetime.now(timezone.utc):
        raise ValueError("Future observations are not accepted")
    if source in {"authenticated_sensor", "authenticated_telemetry"} and record.get("authenticated") is not True:
        raise ValueError("Authenticated source must be verified by trusted ingestion")
    if source == "verified_import" and record.get("verified") is not True:
        raise ValueError("Imported data requires verification")
    return True


def display_status(record):
    if not record:
        return "Brak danych"
    try:
        validate_observation(record)
    except (ValueError, TypeError):
        return "Dane niezweryfikowane — nie wyświetlaj jako pomiar"
    return "Dane rzeczywiste — źródło zadeklarowane"
