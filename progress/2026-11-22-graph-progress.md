# 2026-11-22 · Graph progress and container verification

Queued replay workers now persist a progress event when a LangGraph node completes. Steps share the existing SSE cursor with lifecycle transitions and are written only while the worker's claim token still matches. Existing SQLite event tables gain a nullable step column on startup. The reconnect test checks ordered graph steps. The lease test verifies that an older worker cannot publish a step after reassignment.

The Docker retry built the image and exposed a file-permission issue. Some source captures had root-only read permissions inside the image. The Dockerfile now grants read access to the testbed at build time while keeping the runtime user non-root. The corrected stack completed a real queued investigation over HTTP and passed all three replay evaluations inside the container.

See the [progress streaming lesson](../Concepts/12-progress-streaming.md).

Rebuilt the image with step streaming and verified that the HTTP smoke test sees the validation event and completion. All three evaluations passed inside the container. A legacy SQLite event was also readable after migration. The isolated test containers and temporary volume were removed.
