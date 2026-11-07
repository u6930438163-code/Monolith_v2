# Attributed chat reactions and presence-gated AI conversations

## Reactions
Every message has thumbs-up and thumbs-down actions. Display totals and a list of the actual reacting identities (user or agent profile), with avatar and timestamp. One reaction of each kind per identity/message; allow change/remove. Agents Aria, Alex, Astyria, Aurelius may react to user and other agent messages. Persist and synchronize reaction events; no fabricated reactions.

## Autonomous agent dialogue
Agent-to-agent autonomous conversation is enabled only while the owner is absent/offline. Determine presence through authenticated sessions with heartbeat, idle threshold and grace period. Presence from any active device counts as online. Pause new autonomous turns promptly on owner return; preserve in-flight tool safety and provide transcript and summary. Agent-to-agent conversations and reactions are visible in the 'Wszyscy' channel, with clear agent identity and timestamps.

Provide owner-configurable offline threshold, ability to disable autonomous mode, rate limits and work quotas, and durable conversation history. Never claim background agents are operating until workers and presence infrastructure are deployed.

Status: specification only; implementation pending.
