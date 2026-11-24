# 2026-11-24 · Worker reliability

The worker loop now logs unexpected errors, backs off, and continues instead of exiting. SIGTERM lets the current job finish before the process exits, which matters because the worker is PID 1 in the Compose and Kubernetes images. Queued jobs count their claims; after three unfinished claims the investigation is marked failed instead of being reclaimed forever. Existing SQLite and PostgreSQL tables gain the `attempts` column at startup.

Verified with unit tests for the error loop, the attempt limit, the three failure messages, and an older SQLite schema; a subprocess test that sends SIGTERM to an idle worker; and the Compose smoke script run against a local API and worker on SQLite. The PostgreSQL column migration was not run locally; the CI container job covers that path.

See the [queues and leases lesson](../Concepts/11-queues-and-leases.md).
