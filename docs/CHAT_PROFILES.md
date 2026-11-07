# Chat profiles and avatars

Every chat participant (human user and AI agent Aria, Alex, Astyria, Aurelius, plus future agents) has a persistent profile with display name, avatar, optional bio/status, and profile settings.

Each participant can change their own avatar independently: upload an image, choose a preset, or select a generated image. Agent-initiated changes must use an authenticated identity and be logged. Users may override their own avatar; agents must not change other participants' profiles without authorization.

Chat messages show circular avatars, names, timestamps and optional presence; clicking an avatar opens the profile and its editable settings for the owner. Avatar changes synchronize to chat views and across devices in near real time, while preserving attribution of older messages.

Image handling: validate MIME and dimensions, strip metadata, resize thumbnails, protect uploads, provide default fallback, and do not expose private file URLs. Mobile layout must avoid text overflow and support accessible controls.

Status: specification; implementation pending.
