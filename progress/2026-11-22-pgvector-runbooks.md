# 2026-11-22 · Persistent runbook embeddings

Added an optional pgvector backend for hybrid runbook retrieval. PostgreSQL stores BGE-small vectors by model and content hash. A new process reuses existing vectors, while edited text gets a new key. Search filters to the current corpus before fusing cosine and keyword rankings. The citation records which vector backend was used.

The migration creates a vector column and cosine HNSW index. The checked corpus is small, so no index speedup or recall claim is made. This PostgreSQL integration stores runbook vectors. Incident records and jobs still use SQLite.

See the [persistent embeddings lesson](../Concepts/21-pgvector-persistence.md).

Verified against a temporary PostgreSQL 17 container with pgvector and the real BGE-small model. All three replay evaluations passed. A second process retrieved the expected Payment section while passage embedding was disabled, confirming reuse of five stored vectors. A modified corpus inserted one new vector and returned its own section. Eighteen tests and Ruff passed.
