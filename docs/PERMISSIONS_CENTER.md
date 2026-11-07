# Centrum Uprawnień — Monolith_v2

Scope: **every** application and system element, including the permission manager itself, development center, chat, agent identities, workers, terminal, shell, remote desktop, diagnostics, Ollama, APIs, models, GitHub accounts, missions, spacecraft infrastructure, communications, attachments, explorer, databases, billing, backups and deployment.

Owner is the top-level administrator. Agent identities: Aria, Alex, Astyria, Aurelius. Permission model: deny by default; explicit per-identity, per-resource, per-action grants, roles plus scoped capabilities; inheritance with explicit denies; time-limited delegated permissions; separate read/execute/change/deploy/manage rights. Permissions checked server-side for API, background jobs, UI and CLI; no UI-only enforcement.

Permissions themselves are protected resources. Changes to access controls, credentials, billing, destructive operations, production deployment and root access require owner approval and auditable confirmation. A user can delegate additional powers explicitly; never assume an LLM has unrestricted root authority. Secrets stored in secure runtime secrets manager, never git or chat.

Record immutable audit entries: actor, target, action, time, authorization decision, approval, outcome, correlation ID. Provide permission editor, effective-access explanation, revocation, emergency shutdown, session invalidation and MFA for privileged actions.

Status: specification; implementation pending.
