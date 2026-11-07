# Bootstrap Monolith_v2

Debian 13 / Ubuntu: review `scripts/install.sh` before executing it as root.

In Codespaces, start the loopback-only MVP without root:

```bash
bash scripts/start_mvp.sh
```

This starts the read-only status API. The authenticated chat gateway starts only
when `MONOLITH_BRIDGE_TOKEN` is configured in the environment. The script does
not create or store credentials. Stop only processes started by the script with
`bash scripts/start_mvp.sh stop`; logs and PID files are kept under the user's
state directory, outside the repository. Ollama and LibreChat remain separate
services and are reported according to actual availability.

```bash
bash scripts/install.sh --dry-run
sudo bash scripts/install.sh
bash scripts/verify.sh
```

Optional after installing Ollama separately from the official website:
```bash
sudo bash scripts/install.sh --pull-model
```

Optional Codex CLI installation (requires supported Node/npm):
```bash
sudo bash scripts/install.sh --with-codex
```

To enable services after checking credentials, service account access and installed binaries:
```bash
sudo bash scripts/install.sh --enable-services
```

The default bootstrap does NOT install LibreChat or Docker, expose ports, start services, or log in to Codex. It creates a random service token in `/etc/monolith/bridge.env`, never in Git. Ollama installation is deliberately manual to avoid blindly piping an internet script to root. Service templates are generated for a restricted system account.

**Important:** `monolith-codex.service` uses `ProtectSystem=strict` and read-only Codex mode; it needs the Codex binary available on the service PATH and an authenticated Codex session or supported credential setup for the service account. The installer does not establish those. Do not assume `--enable-services` guarantees successful Codex operation. The installed bridge is loopback-only and is not a LibreChat plugin yet.

This is a first-stage bootstrap, not a one-command complete application deployment. Verify your hardware resources before pulling 11B.
