# Real Vision and DALL-E 3 — Monolith_v2

## Real Vision via Ollama
- Primary vision model: llama3.2-vision:11b (verify installed Ollama model tag).
- Chat attachments: image analysis, screenshots, document images; video through sampled frames, with timestamps.
- Backend proxy to Ollama must support image payloads, size limits, timeouts, streaming responses, and diagnostics.
- Ollama URL is configurable and must be reachable from the backend container; localhost inside the browser or container is not necessarily the host.
- Show actual model/provider and errors; never pretend to have processed an image if the model is unavailable.

## DALL-E 3
- OpenAI image generation via server-side API key and supported image-generation endpoint.
- Generate avatars, spacecraft and facility concept images, mission visualizations, and chat attachments.
- User and AI agents can choose their own avatars; store generated image with profile permission and audit trail.
- Check current provider availability, API parameters and model lifecycle before implementation; provide a configurable newer image-model alternative.
- Clearly label generated imagery as conceptual, not real-world telemetry.

## UX
- Main LibreChat message composer: image upload, Analyze with Real Vision, Generate image, Choose as avatar.
- Persist media metadata, owner, timestamps, provider and model; sync changes across clients.
- Require explicit authorization for changes to other profiles and for paid generation actions according to budget policy.

Status: specification only. API connectors and UI not yet implemented or verified.
