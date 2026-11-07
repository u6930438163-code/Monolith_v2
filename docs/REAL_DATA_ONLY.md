# MONOLITH_V2 — REAL DATA ONLY

**Global operational requirement:** no fabricated, simulated, synthetic or demo data in operational dashboards, fleet maps, botany, diagnostics, transmissions or mission reports.

## Mandatory source rules
1. Real measurements require an identified source, UTC timestamp and provenance.
2. Hardware data must be authenticated at a trusted ingestion boundary. Never trust a user-supplied `authenticated: true` field without server-side verification.
3. Operator observations are labeled manual; imported datasets require integrity and origin checks.
4. AI interpretations must be kept separate from measured values, linked to underlying evidence and labeled unverified until reviewed.
5. Missing data must remain missing. Never replace with plausible values.
6. Experimental hypotheses and unknown signal classifications are not claims of verified physics.
7. If a sensor disconnects, show stale/disconnected status; do not silently continue with generated positions.
8. Do not use sample/demo datasets in production views.

## Implementation status

`core/real_data_policy.py` provides an initial validation gate. It does **not** establish cryptographic authenticity and is not yet wired into existing registries or LibreChat. Existing modules may still accept simulation types, and the current ChatGPT solar-map demonstration contains simulated objects. Those must be removed or migrated before claiming production-wide enforcement.

## Migration tasks
- Remove simulation options from operational APIs and UIs; keep historical entries marked non-operational.
- Apply source validation server-side to fleet positions, contacts, botany, and transmissions.
- Require signed/authenticated ingestion for sensor and telemetry feeds.
- Replace demo ship positions and signals with explicit empty states until connected.
- Add integration tests to ensure simulated data cannot enter production.
