# 2026-11-22 · Checkpointed human approval

PostgreSQL-backed plans now pause at a LangGraph interrupt. The approval route verifies the active plan and resumes its saved thread. Edits close the old thread and pause a new thread for the replacement. Plan state and approval history commit together with the approval checkpoint. SQLite mode continues to produce the dry-run preview through the local transaction.

Verified on PostgreSQL 17 with a queued investigation, a fresh store instance, an edit, and approval of the replacement. An injected failure after graph resumption rolled back both the checkpoint and the decision. The next approval resumed the interrupted thread and produced the saved preview.

See the [checkpoint and interrupt lesson](../Concepts/27-langgraph-checkpoints.md).
