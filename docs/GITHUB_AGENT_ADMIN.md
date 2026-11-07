# GitHub administrative access — Monolith_v2

Owner: Super Administrator. AI agent identities: Aria, Alex, Astyria, Aurelius, each authorized to perform administrative GitHub operations through the Monolith backend.

Capabilities: repository management, branches, files, commits, issues, pull requests, workflows, Codespaces, webhooks, collaborators and settings, subject to actual GitHub token/App permissions and platform API limitations.

Security: per-agent service identity and audit attribution; encrypted server-side tokens; separate account connections; permissions bounded by owner-configured GitHub grants; no frontend exposure of tokens. Require owner confirmation for irreversible/destructive operations (repository deletion, access changes, force pushes, secret changes). Never bypass GitHub permissions. Support revocation, rate limits, and operation logs.

Status: authorization design specification only. No tokens or admin grants provisioned, no agents deployed.
