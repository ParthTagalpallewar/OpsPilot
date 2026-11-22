# Embeddings and hybrid runbook search

Keyword ranking rewards matching terms. An embedding model maps a query or a runbook section to a vector. Cosine similarity compares their directions, which can uncover relevant sections when the query and runbook use different wording.

OpsPilot can run both searches. The keyword path uses SQLite FTS5. The semantic path uses FastEmbed with BGE-small and scores sections mentioning the selected service. Reciprocal rank fusion combines both lists by adding `1 / (60 + rank)` for each appearance. Agreement raises the combined score, and a section can appear through just one search.

A citation keeps the selected file, heading, line, and excerpt. In hybrid mode it also records the model and the ranks contributed by each search. Similarity and rank indicate retrieval relevance. The telemetry still establishes which events occurred.

## Practice

Install the optional model dependency from the README. Compare keyword and hybrid results for the Payment symptom “authorization refused.” Inspect the retrieval ranks. Then change the query to “payment failure invalid token” and see where the two rankings agree.

See the [FastEmbed retrieval guide](https://qdrant.github.io/fastembed/qdrant/Retrieval_with_FastEmbed/).
