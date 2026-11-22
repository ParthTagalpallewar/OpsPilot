# 2026-11-22 · Shared PostgreSQL and Redis demo

Added a Compose overlay that runs OpsPilot API and workers with PostgreSQL and Redis. The shared image installs the PostgreSQL checkpoint and Redis client extras. The database and Redis stay on the Compose network, and the PostgreSQL volume persists reports, decisions and graph checkpoints.

CI now exercises the same queued replay, citation, event stream, and approval flow in SQLite and shared modes. The shared job additionally checks for both saved approval threads.

See the [container and CI lesson](../Concepts/15-containers-and-ci.md).

Concurrent startup exposed a migration deadlock between an advisory lock waiter and LangGraph's concurrent index creation. Switched schema setup to short autocommit lock attempts. Six processes then initialized the same fresh PostgreSQL database successfully.

The full HTTP smoke test passed with separate API and worker processes connected to PostgreSQL 17 and Redis 7. PostgreSQL contained both approval threads, and Redis recorded the worker's blocking read and the API's wake-up push. Both Compose configurations rendered and twenty-three tests passed. The shared container build was still downloading its PostgreSQL client wheel at this checkpoint.
