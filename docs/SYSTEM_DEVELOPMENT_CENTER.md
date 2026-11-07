# Centrum Rozwoju Aplikacji i Systemu — Monolith_v2

Development management applies to **each** component and subcomponent, including this center and permissions: chat/mentions/reactions/presence, AI agents and workers, Ollama/models, vision/images, terminal, remote diagnostics, infrastructure, missions/ETA, hyperspace communication, attachments, explorer, knowledge bases, GitHub integration, budgets, database, UI/mobile, security, backend, infrastructure and deployment.

Every component has a registry entry: stable ID, owner, repository paths, running version, dependencies, health, tests, recent changes, roadmap, permission scopes, last deploy, rollback target. Expose actions: inspect, propose feature/fix, assign agent, edit source, run isolated tests, review diff, approve, deploy, rollback and view audit trail.

Workflow: request -> issue/task -> implementation branch or explicitly authorized direct edit -> lint/tests/security checks -> review/owner approval where required -> deployment -> monitoring -> rollback on regression. Agent autonomy is bounded by authorization and resource limits. Show real results from connected GitHub/CI/runtime, not fabricated completion percentages. Real-time sync via authenticated events and durable event history.

Integrate with GitHub Actions and Codespaces when connected. Production system modification, secrets, permissions, spending and destructive changes require explicit owner approval. Remote changes must not silently modify production hosts.

Status: specification; actual dashboard and orchestration pending.
