# 2026-11-22 · Local incident intake

Added a FastAPI application factory for local replay and a SQLite investigation store. The HTTP contract accepts an explicit demo scenario with a title and description. It stores the completed report and retrieves it by investigation ID. The API returns 201 for the synchronous local replay. The queued 202 workflow, free-text triage, and shared PostgreSQL storage are still planned.

See [Incident intake and persistence](../Concepts/05-incident-api-and-persistence.md) and the [replay evaluation milestone](2026-11-22-replay-evaluation.md).

Verified the FastAPI application at the ASGI boundary, including 201 creation, 200 retrieval from a fresh application instance, 404 for an unknown ID, 422 for a blank title, and 503 for unavailable captures. Verified three concurrent SQLite writes and retrieval from a new store. The workspace denied binding a loopback socket, so the Uvicorn network smoke test could not run here.
