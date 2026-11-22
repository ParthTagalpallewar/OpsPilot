# 2026-11-22 · Durable local replay queue

Added an opt-in HTTP 202 workflow and a separate worker process. SQLite commits investigation creation and enqueue together. Workers claim queued or expired jobs and persist the final outcome only if their claim token still matches. Synchronous replay remains available and completed queued investigations use the same report and approval logic.

This uses a local SQLite queue. The planned Redis worker, shared PostgreSQL storage, and server-sent progress events are pending.

See the [queue and lease lesson](../Concepts/11-queues-and-leases.md).

Verified HTTP 202 at the ASGI boundary and ran a separate worker process against the same database. The API then returned the completed report and dry-run plan. The tests also simulate lease expiry and confirm that the previous worker cannot overwrite the result.
