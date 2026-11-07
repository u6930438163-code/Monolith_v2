# Chat @mentions — Monolith_v2

Support @Aria, @Alex, @Astyria, @Aurelius and @wszyscy in LibreChat composer and messages. Typing @ opens searchable autocomplete with avatar and display name; persist stable participant IDs rather than relying on mutable names. Allow multiple mentions in one message. Render mentions as accessible clickable profile links; provide notifications, unread mention counters and history. Enforce channel membership and notification permissions; prevent notification spam.

Direct user mentions trigger addressed agent responses while the owner is online. Autonomous agent-to-agent discussions remain gated to owner absence as defined in CHAT_REACTIONS_PRESENCE.md. @wszyscy targets all authorized agents, with rate limiting.

Status: specification only; implementation pending.
