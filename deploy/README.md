# Deployment scaffolding (Debian/Ubuntu)

These systemd files are **templates**, not deployed services. They require an existing restricted `monolith` user, checked-out source in `/opt/monolith`, and an installed/authenticated Codex CLI available to that account. Codex currently runs read-only; do not enable writable sandbox without owner approval.

## Setup checklist
1. Install Python 3.11+ and optional `psutil`; install Ollama separately and pull `llama3.2-vision:11b` on an appropriately provisioned host.
2. Create dedicated service account and `/var/lib/monolith-codex` with owner `monolith` and mode 0700. Protect `/opt/monolith` from writes by untrusted accounts.
3. Create `/etc/monolith/bridge.env` with mode 0600, containing `MONOLITH_BRIDGE_TOKEN=<random 48+ character token>` and `OLLAMA_API_URL=http://127.0.0.1:11434`. Do not commit it.
4. Review and copy service files to `/etc/systemd/system/`; adjust `ExecStart` for virtualenv and the Codex binary path. Ensure the worker account can authenticate with Codex securely.
5. Run `python3 -m unittest discover -s tests -v` before starting services. Use `systemctl daemon-reload`, then start/enable services only after verifying permissions and environment.
6. Check `systemctl status monolith-bridge monolith-codex` and `journalctl -u monolith-bridge -u monolith-codex`. The bridge listens on loopback only.

## Limitations
LibreChat is not yet deployed or connected. No production authentication/agent permission adapter exists. Do not expose the bridge, Codex CLI or Ollama API directly to the internet. Remote desktop and agent autonomous chat remain unimplemented. The worker is a prototype and lacks robust job lease recovery/cancellation; supervise carefully.
