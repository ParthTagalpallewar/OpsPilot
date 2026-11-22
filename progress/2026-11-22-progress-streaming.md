# 2026-11-22 · Progress streaming and evidence lookup

Added a server-sent event endpoint backed by a durable SQLite event table. The queue commits lifecycle transitions and progress events together. The endpoint replays later events after a valid cursor and returns 204 when the client has already received the terminal event. Existing completed reports can stream a terminal snapshot.

Added an investigation-scoped evidence endpoint because the same frozen evidence IDs can appear in multiple reports. This milestone streams job lifecycle changes. Per-node progress and Redis-backed delivery remain pending.

See the [progress streaming lesson](../Concepts/12-progress-streaming.md).

Verified that a client holding the queued event can reconnect and receive only running and completed events. A subsequent reconnect receives 204. Also verified citation lookup and unknown-evidence handling at the ASGI boundary. Twelve tests and all three replay evaluations passed.
