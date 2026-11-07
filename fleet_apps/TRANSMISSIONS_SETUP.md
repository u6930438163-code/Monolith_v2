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
