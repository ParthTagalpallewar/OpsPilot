# 2026-11-22 · Hybrid runbook retrieval

Added an opt-in FastEmbed BGE-small semantic ranker. The local retriever combines cosine similarity results and SQLite BM25 rankings through reciprocal rank fusion. It preserves the keyword baseline by default. Hybrid results include the model name, query and contributing ranks. Passage vectors are cached by section content in the process.

Tests cover semantic-only retrieval and rank fusion agreement. This implementation scans the small runbook corpus locally. Persisted embeddings, pgvector indexing, and evaluation on a larger corpus remain pending.

See the [hybrid search lesson](../Concepts/20-hybrid-runbook-search.md).

Verified with the downloaded BGE-small model. “Authorization refused” retrieved the Payment investigation section at semantic rank one with no keyword match. “Payment failure invalid token” returned the same section at rank one in both searches. All three replay evaluations passed in both retrieval modes, and all eighteen tests passed.
