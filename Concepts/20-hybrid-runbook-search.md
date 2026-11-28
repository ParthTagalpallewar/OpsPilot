# Embeddings and hybrid runbook search

Keyword ranking rewards matching terms. An embedding model maps a query or a runbook section to a vector. Cosine similarity compares their directions, which can uncover relevant sections when the query and runbook use different wording.

OpsPilot can run both searches. The keyword path uses SQLite FTS5. The semantic path uses FastEmbed with BGE-small and scores sections mentioning the selected service. Reciprocal rank fusion combines both lists by adding `1 / (60 + rank)` for each appearance. Agreement raises the combined score, and a section can appear through just one search.

A citation keeps the selected file, heading, line, and excerpt. In hybrid mode it also records the model and the ranks contributed by each search. Similarity and rank indicate retrieval relevance. The telemetry still establishes which events occurred.

## How OpsPilot combines the rankings

**OpsPilot uses equal-weight reciprocal rank fusion (RRF).** Each search contributes `1 / (60 + rank)` for every section in its result list. Rank starts at 1. A section absent from a list contributes zero from that list. The value `60` is the constant in the formula. The keyword and semantic lists both use the same formula and each has an implicit weight of 1. [Fusion code](../opspilot/evidence/runbooks.py#L99)

For example, suppose a query about high Ad CPU produces these rankings:

| Section | Keyword rank | Semantic rank | RRF score |
|---|---:|---:|---:|
| General Ad CPU checks | 1 | — | `1/61 ≈ 0.0164` |
| Investigate sustained Ad CPU | 2 | 1 | `1/62 + 1/61 ≈ 0.0325` |
| Ad processor saturation | — | 2 | `1/62 ≈ 0.0161` |

“Investigate sustained Ad CPU” wins in this example because it appears near the top of both lists. Using positions lets the fusion combine SQLite BM25, where smaller scores rank higher, with cosine similarity, where larger scores rank higher. The code picks the highest fused score, then uses keyword position and original section index as tie-breakers. With only one ranking available, its first result wins. [Winner selection](../opspilot/evidence/runbooks.py#L105)

### Where weights apply

- **Inside keyword search**, BM25 weights heading matches more heavily than excerpt matches. That can affect the keyword order before fusion. [BM25 call](../opspilot/evidence/runbooks.py#L30)
- **At fusion**, each list has equal influence per rank. A weighted RRF variant could multiply the keyword contribution by 2 and the semantic contribution by 1. A weighted raw-score approach would instead combine the underlying scores after putting them on a compatible scale. The implementation uses rank positions with the same contribution from either list.

The semantic path uses the same embedding model for the query and the candidate sections. It considers sections that mention the selected service. Without a vector DSN, Python scores the candidates in memory and keeps up to five above or equal to the similarity cutoff of `0.35`. With a vector DSN, pgvector orders the candidate embeddings by cosine distance and returns up to ten. Both backends produce an ordered list for RRF. [Candidate selection](../opspilot/evidence/runbooks.py#L77) · [In-memory ranking](../opspilot/evidence/embeddings.py#L32) · [pgvector ranking](../opspilot/evidence/vector_store.py#L43)

## Practice

Install the optional model dependency from the README. Compare keyword and hybrid results for the Payment symptom “authorization refused.” Inspect the retrieval ranks. Then change the query to “payment failure invalid token” and see where the two rankings agree.

See the [FastEmbed retrieval guide](https://qdrant.github.io/fastembed/qdrant/Retrieval_with_FastEmbed/).
