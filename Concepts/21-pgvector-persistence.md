# Persistent embeddings and vector indexes

The in-memory hybrid search embeds each runbook section and caches the vector in the process. A PostgreSQL backend can reuse those vectors across CLI invocations and worker processes. OpsPilot keys a stored vector by the embedding model and a SHA-256 hash of the passage text. Editing the text changes the key, so the next search embeds the new content. Queries only consider keys from the current corpus.

The pgvector column stores 384 components for BGE-small. Its `<=>` operator computes cosine distance. Smaller distances indicate more similar directions. OpsPilot combines the resulting ranking with the existing keyword ranking.

The migration adds an HNSW index for cosine distance. PostgreSQL may use an exact scan for a small corpus. For a larger corpus, an approximate index can improve latency at the cost of missing some neighbors, especially with restrictive filters. Compare query plans and retrieval quality before tuning an index.

## Practice

With the pgvector backend enabled, replay Payment twice. Query the count of `runbook_vectors` rows between runs. Then edit a copy of a Payment runbook section and search again. Observe the new row and the updated citation.

See the [pgvector indexing guide](https://github.com/pgvector/pgvector#indexing).
