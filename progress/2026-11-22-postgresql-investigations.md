# 2026-11-22 · PostgreSQL investigation storage

Added an optional PostgreSQL backend for investigation documents, durable jobs, status and graph events, alert deduplication, trace context, and approvals. The API and worker select it with the same DSN environment variable. The existing SQLite API and worker keep working by default.

Verified against temporary PostgreSQL 17 with concurrent webhook delivery, two separate worker processes, SSE replay and concurrent approval attempts. One alert occurrence produced one completed investigation. One approval was stored and the competing decision returned HTTP 409.

This backend serializes short writes with a database advisory lock. Replay runs outside that lock. Redis delivery, LangGraph checkpoint resumption, and migration of old SQLite datasets remain pending.

See the [PostgreSQL storage lesson](../Concepts/22-postgresql-investigation-storage.md).
