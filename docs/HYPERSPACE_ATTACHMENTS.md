# Hyperspace communications — attachments

Hyperspace communications is the product name for internet-based messaging between authorized users, spacecraft and facility endpoints. It does not imply faster-than-light transport.

Support bidirectional attachments: images, videos, documents, archives, SQLite databases, source files and arbitrary opaque binary payloads. Preserve original bytes and metadata; do not require displaying raw binary data.

Design: upload/download API, chunked/resumable transfer, per-file size limits, end-to-end integrity hashes, transfer IDs, progress, retries, delivery acknowledgement, access controls, encryption in transit and at rest, optional end-to-end encryption, audit logs and malware scanning/sandboxed inspection.

Distinct statuses: queued, uploading, transmitted, delivered, downloaded, opened (only with recipient-side confirmation), failed. Do not infer unique human recipients from IPs or connections.

Agents can prepare and analyze attachments through Ollama vision or safe parsing tools; outbound sending requires appropriate authorization. Unknown binary formats and claimed extraterrestrial origin must remain unverified until evidenced.

Status: design specification only; network transfer implementation pending.
