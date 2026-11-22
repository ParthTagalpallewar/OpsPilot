# 2026-11-22 · Redis worker notifications

Added optional Redis signaling for queued work. The API sends a bounded, short-lived wake-up hint after the database transaction commits. A worker waits on Redis when idle, then claims a job from the database. Redis timeouts and outages fall back to polling.

This uses Redis for wake-ups. SQLite or PostgreSQL remains responsible for durable jobs, retry leases, and ordered SSE events. Redis event broadcasting and checkpoint resumption remain pending.

See the [Redis notification lesson](../Concepts/23-redis-worker-notifications.md).

Verified a separate worker blocked on Redis 7, then processed a job submitted through the signaling store. It completed another queued replay after the Redis container stopped. A unit test verifies notification happens after the job is visible. Nineteen tests, all three replay evaluations, and Ruff passed.
