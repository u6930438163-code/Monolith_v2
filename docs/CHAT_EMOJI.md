# Emoji and reactions — Monolith_v2

LibreChat main chat supports Unicode emoji, searchable emoji picker, skin tone variants, emoji in profile names, mission names, spacecraft and facility labels.

Reactions: thumbs up/down, heart, laughter and custom emoji; users and authenticated AI agents may react to messages. Reaction clicks update state without sending a new chat message. Persist reaction identity and timestamps, synchronize across connected clients and provide undo/remove.

Custom emoji/stickers: allow safe image uploads and generated avatars/stickers with ownership, permissions, file-size limits, metadata removal and content validation. DALL-E 3 integration remains separately pending.

Mobile: native emoji keyboards, accessible touch targets, fallback fonts, correct rendering of combined Unicode emoji and no horizontal overflow.

Status: specification only, UI/backend implementation pending.
