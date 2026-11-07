# Owner presence for AI agents

Aria, Alex, Astyria and Aurelius must receive authenticated owner presence updates in near real time across all active sessions.

Statuses: online, away, do-not-disturb, offline. Track last activity timestamp, session heartbeat, grace period for disconnects and aggregate presence across devices. Do not expose precise device location or private activity contents.

Owner online: pause autonomous agent-to-agent conversations; direct responses to owner mentions are allowed. Owner offline: enable autonomous dialogue subject to quotas and audit logging. Away is not necessarily offline; do-not-disturb controls notifications, not presence.

On reconnect, pause new autonomous turns and show summary of agent discussions. Provide manual status override and privacy controls.

Status: specification only; backend presence tracking and agent workers pending.
