# Original agents: Bastilla LIVE integration (Monolith_v2)

Source repository: https://github.com/u6930438163-code/Bastilla_1_2
Source contracts: docs/LIVE_CHAT_SETUP.md and docs/LIBRECHAT_INTEGRATION.md.

## Verified repository facts

- Bastilla LIVE uses authenticated operator sessions, persistent message queues, and four independently authenticated worker tokens.
- A worker heartbeat means that transport is alive; it does not prove the underlying model can respond.
- Bastilla LIVE requires actual worker adapters for Aria, Alex, Astyria, and Aurelius. GitHub Copilot agent profiles and SVL_System chat roles are NOT executable original workers.
- The LibreChat bridge expects a running Bastilla LIVE API, not only source files. It cannot be pointed at GitHub and treated as a running service.
- The Monolith `agents/connection.py` contract is different: HTTPS POST {"message":"...","agent":"Aria"} with Bearer auth, response {"reply":"..."}. Do not point it at Bastilla's login or queue endpoint without an adapter.

## Minimal deployment path

1. Run the four real workers against Bastilla LIVE **or** migrate its queue/worker runner into the Monolith backend. Only one host service is necessary after migration, but the worker processes still have to run somewhere.
2. Create a server-side adapter per agent that implements Monolith's HTTPS POST/Bearer/reply contract, authenticates to the LIVE API, queues a message to the matching worker, waits for its real response, and returns HTTP 503 if no authenticated worker is available. Do not generate substitute replies.
3. Set `MONOLITH_AGENT_ARIA_URL` and `MONOLITH_AGENT_ARIA_TOKEN` on the Monolith host. Repeat for ALEX, ASTYRIA, AURELIUS. Keep credentials out of Git and the browser.
4. Run one real end-to-end message through each configured worker before declaring connected. For the shared channel, the Monolith backend sends to each configured endpoint.

## Current state

Repository integration research complete; no runtime endpoint or token has been supplied or verified. **Agents are not yet connected.** Do not represent this document or a configured profile as a live integration.

Monolith's `MONOLITH_PASSWORDLESS=true` is intended only for a private/trusted environment; keep any publicly reachable agent bridge authenticated and do not expose privileged APIs to untrusted users.
