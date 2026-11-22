# 2026-11-22 · Runbook retrieval

Added six troubleshooting and recovery sections across three demo runbooks. The LangGraph workflow retrieves one relevant section with SQLite FTS5 and BM25, adds it as cited guidance, then validates the combined report. Runbooks are read from a sibling directory of the scenario captures. A missing corpus yields an empty guidance list.

The evaluation now requires the expected runbook section for each scenario. This milestone implements local keyword retrieval. Embeddings, pgvector, hybrid ranking, and model-augmented generation remain pending.

See the [runbook retrieval lesson](../Concepts/08-runbook-retrieval.md) and the [LangGraph milestone](2026-11-22-langgraph-replay.md).
