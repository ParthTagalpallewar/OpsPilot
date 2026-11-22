# 2026-11-22 · Container demo and CI

Added a Docker image with locked dependencies and a non-root runtime user. The demo Compose stack runs a FastAPI container and a worker from the same image, with a shared SQLite volume and a loopback-bound API port.

CI now runs the replay evaluator alongside lint and tests. A separate job builds the demo and exercises the real HTTP queue-to-worker flow. The existing developer infrastructure Compose file still provisions PostgreSQL and Redis. Kubernetes deployment and backend integration remain pending.

See the [container and CI lesson](../Concepts/15-containers-and-ci.md).

Compose configuration, the lockfile, Ruff, thirteen tests, and all three replay evaluations passed. The HTTP smoke script also passed against a local Uvicorn API and separate worker, including evidence lookup and the terminal SSE event. The first Docker build timed out downloading a Linux wheel. A retry with a longer download timeout was still in progress at this checkpoint.
