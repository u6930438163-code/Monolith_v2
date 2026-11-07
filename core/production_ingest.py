"""Strict operational ingestion boundary for Monolith fleet telemetry.

Only trusted, preconfigured adapters can submit records. The adapter token is
an application-side capability, not a client-supplied 'verified' boolean.
"""
import hmac
import math
from datetime import datetime, timezone
from fleet_apps.solar_positions import FleetPositions

class ProductionFleetIngest:
    def __init__(self, db_path, *, trusted_adapters):
        if not isinstance(trusted_adapters, dict) or not trusted_adapters:
            raise ValueError("Configure trusted adapters before ingestion")
        self.adapters = dict(trusted_adapters)
        self.positions = FleetPositions(db_path)

    def ingest_position(self, *, adapter_id, adapter_token, ship_id, observed_at,
                        x_au, y_au, z_au, mission="", status="unknown"):
        expected = self.adapters.get(adapter_id)
        if not isinstance(expected, str) or not isinstance(adapter_token, str) or not hmac.compare_digest(expected, adapter_token):
            raise PermissionError("Untrusted telemetry adapter")
        if not isinstance(ship_id, str) or not ship_id.strip():
            raise ValueError("Ship ID required")
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) for v in (x_au, y_au, z_au)):
            raise ValueError("Invalid coordinates")
        try:
            stamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as exc:
            raise ValueError("UTC timestamp required") from exc
        if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError("UTC timestamp required")
        if stamp > datetime.now(timezone.utc):
            raise ValueError("Future observations forbidden")
        # Existing registry agent field is an attribution label, not authentication.
        return self.positions.report(
            ship_id=ship_id, agent="Alex", source="telemetry",
            source_ref="trusted-adapter:" + adapter_id,
            observed_at=stamp.isoformat(), x_au=x_au, y_au=y_au, z_au=z_au,
            mission=mission, status=status)

    def latest(self):
        # Legacy storage may contain simulation rows; never expose them in production.
        return [row for row in self.positions.latest() if row["source"] == "telemetry"
                and row["source_ref"].startswith("trusted-adapter:")]

    def close(self):
        self.positions.close()
