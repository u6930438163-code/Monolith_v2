# Monolith Diagnostic Center

Run the local read-only collector with `python3 diagnostics/collector.py`. Optional: `pip install psutil` for CPU, memory and uptime metrics. This is an initial working diagnostic script, not yet integrated with LibreChat or deployed on a remote host.

Planned diagnostic categories: CPU/RAM/processes, disk SMART and filesystem, systemd/journal logs, network latency/DNS/routes/WAN, SSH and TLS, containers and Kubernetes, GPU and Ollama, API model health, database and backups, GitHub workflows/Codespaces, security configuration and agent worker state.

Agent-specific dashboard: Aria, Alex, Astyria, Aurelius each has tool access granted per host, live logs, incident queue, diagnosis, proposed repair and verified result. Display exact source, timestamp and errors. No simulated status.

Remote desktop: authenticated RDP/VNC/Guacamole gateway with TLS, MFA, session audit and explicit owner consent. Do not expose RDP/VNC directly to the public internet. All repair commands require scoped authorization and destructive actions require owner approval. Never give LLM output unrestricted shell execution.

Planned tools include psutil, btop, htop, journalctl, smartctl, nvme-cli, lsof, strace, perf, ss, ip, dig, mtr, tcpdump, nmap (authorized targets only), curl, openssl, docker, podman, kubectl, prometheus, node_exporter, grafana, loki, falco, trivy, osquery, auditd, lynis, ollama API, nvidia-smi, git and GitHub API. Install only supported packages on a controlled host after reviewing permissions and licensing.
