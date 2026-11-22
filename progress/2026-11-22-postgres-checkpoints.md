# 2026-11-22 · PostgreSQL-backed graph recovery

The PostgreSQL worker now uses a LangGraph checkpoint saver keyed by investigation ID. The saver writes synchronously between graph steps. A per-thread session lock serializes graph execution, and the existing lease token still fences result and progress writes.

Verified against PostgreSQL 17 by ending a worker process at the report step after collection. A second process reclaimed the job and finished using the stored evidence after the temporary capture files had been removed. The progress history contained one collection and one completion.

SQLite demo workers still restart the replay from its initial inputs after a crash. Approval decisions remain a separate persisted flow. Resuming a graph after a human approval interrupt is pending.

See the [checkpoint lesson](../Concepts/27-langgraph-checkpoints.md).
