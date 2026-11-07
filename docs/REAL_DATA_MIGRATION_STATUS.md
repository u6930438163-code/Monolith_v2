# Real-data-only migration status

Implemented:
- Strict, opt-in fleet telemetry ingestion through `core.production_ingest.ProductionFleetIngest`.
- Trusted adapter token check before recording positions.
- UTC timestamp checks and future-date rejection.
- Production listing filters out legacy simulation and AI-estimate rows.
- Unit tests for authentication, empty state, and timestamp rejection.

Not implemented / limitations:
- This is a new trusted ingestion entry point, not yet wired to a running API or map.
- The legacy `fleet_apps.solar_positions`, `fleet_apps.contacts`, `botany.garden`, and `fleet_apps.transmissions` modules still accept simulated entries. **Do not expose these legacy interfaces to production operators.**
- A configured adapter token proves possession of a secret, not the physical authenticity of a sensor reading. Production requires device attestation/signatures, transport security, replay protection, and per-device authorization.
- The adapter attribution currently uses the legacy `agent` field with a fixed label; this is not proof that the agent produced a reading.
- Tests are committed but have not been verified on the deployment host.

Next priority: replace legacy writers with a single authenticated production API and remove simulation choices from all UI and CLI routes. Until then, the system-wide real-data-only policy is **not fully enforced**.
