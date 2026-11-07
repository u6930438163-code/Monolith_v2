# Ubuntu Control Center — first executable backend

Run from repository root:
```bash
python3 -m control.ubuntu status ollama --actor aria
python3 -m control.ubuntu logs monolith-bridge --actor alex
```

The CLI accepts only three actions (`status`, `logs`, `restart`) for three named services. Restarts require an optional, narrowly-scoped sudoers policy installed by the Ubuntu administrator, validated with `visudo -cf`. The policy is not installed automatically. No generic root shell or unreviewed remote command execution is provided.

**Security:** `--actor` is a label, NOT authentication. Do not expose this CLI as an unauthenticated HTTP endpoint. A future LibreChat integration must verify caller identity, apply centrally stored owner-delegated permissions, rate limits and audit events. Agents can then act without prompting on every approved-in-advance operation. Critical destructive actions and new privilege grants remain out of scope until a robust policy and recovery mechanism exist.

`MONOLITH_CONTROL_AUDIT` can point to a writable append-only log path for recording outcomes. Logging is best-effort and does not replace tamper-resistant central audit storage. Not running on any Ubuntu host yet.
