# Durable LangGraph checkpoints

A queue lease lets another worker claim work after a process stops. A checkpoint tells that worker where to resume. OpsPilot uses the investigation ID as the LangGraph thread ID and saves state in PostgreSQL at step boundaries. A replacement worker reads the saved state and continues from the next pending node.

Synchronous durability waits until the checkpoint is saved before the graph starts the next step. A PostgreSQL session lock serializes execution for one thread. After a process crash, the connection closes and releases the lock. The database claim token still controls which attempt can publish progress and finalize the investigation.

The checkpoint contains evidence already read from the capture. The next pending node can reuse it after a crash, although a node interrupted mid-run may need to run again. Progress events and checkpoints are written separately, so an interrupted run can finish even if an event for an earlier saved step is missing.

## Practice

Run the PostgreSQL worker on a test database. Inspect the saved thread state with `get_state` after a replay. Compare the stored evidence and next-node list with the report and progress events.

See the [LangGraph durability guide](https://docs.langchain.com/oss/python/langgraph/durable-execution).

## Pause for human review

Each PostgreSQL-backed plan version gets its own approval thread. The graph calls `interrupt()` with the plan ID and hash, persists its state, and returns control while the reviewer decides. An accepted decision resumes that thread with `Command(resume=...)`. An edit closes the old thread and opens a new interrupt for the revised plan.

The approval checkpoint and audit event use the same PostgreSQL transaction. If the transaction fails after the graph resumes, the saved thread returns to its interrupted state. The reviewer can retry against the same plan. The resumed graph only prepares the dry-run preview.
