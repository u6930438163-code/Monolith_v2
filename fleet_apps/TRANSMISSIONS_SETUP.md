# Contact transmission investigation: initial integration

This is a working local **request registry**, not a receiver or live agent orchestration system.

## Terminal

From repository root:

```bash
python3 -m fleet_apps.transmission_cli --db transmissions.sqlite3 request contact-01 \
  --agent Astyria --kind hyperspace_simulation \
  --source-ref demo://contact-01 --requested-by owner
python3 -m fleet_apps.transmission_cli --db transmissions.sqlite3 list contact-01
python3 -m unittest tests.test_transmissions -v
```

## Chat and map integration contract

When the operator selects a contact and clicks "Investigate transmission", the authenticated backend should:
1. Resolve the selected contact ID from the contacts registry.
2. Verify the operator's permission to inspect that contact and source.
3. Submit a request to the investigation registry.
4. Return the investigation ID and `queued` status to the UI.
5. Dispatch only approved sources to an agent worker, with audit logs.
6. Stream progress and verified results back to chat and map.

Do not trust user-supplied `requested_by` or `assigned_agent` as authentication. The current CLI is for local, trusted operators only. No RF capture, network interception, autonomous agent dispatcher or live LibreChat integration has been deployed.

`hyperspace_simulation` is explicitly simulated and does not represent a physically verified hyperspace transmission.

## Authenticated HTTPS source for the Monolith web UI

The web UI's **Hiperprzestrzeń** panel uses a separate, read-only outbound HTTPS API contract. It does not use this request registry, a simulation, a radio receiver or a signal-decoding pipeline. Configure the actual source URL and its bearer token in the backend environment only:

```bash
MONOLITH_HYPERSPACE_URL=https://YOUR-REAL-SOURCE.example/api/transmissions
MONOLITH_HYPERSPACE_TOKEN=YOUR_SECRET
```

The source must return HTTP 200 without redirects and a JSON object in this form:

```json
{"transmissions":[{"source":"authenticated-source-id","timestamp_utc":"2026-01-01T00:00:00Z","message":"verified payload"}]}
```

Each record is checked for non-empty string fields; responses are size- and count-limited. Redirects, plain HTTP, unauthenticated responses, invalid records, and unavailable sources produce `not_connected` with no displayed transmissions. The web server reports only the source origin, never the configured path or bearer token. No compatible source endpoint or token was available during implementation; the feature remains unconnected until a real source is configured and successfully returns this contract.
