# Runbook retrieval and BM25

A runbook records troubleshooting steps. OpsPilot splits each Markdown document at its level-two headings so an investigation can cite a specific section. The [Payment runbook](../testbed/runbooks/payment-failures.md) contains one section for diagnosis and another for checking recovery.

The graph builds a query from the service, scenario words, and the first captured warning message when available. SQLite FTS5 stems related words such as “failure” and “failures.” BM25 ranks matching sections using how often terms appear in a section, how common they are across the collection, and how long each section is. OpsPilot gives title matches more weight and returns one ranked section.

The report's guidance cites the section by evidence ID. The record includes its heading, line, excerpt, and search query. A match can tell an operator what to check. Confirmation of the cause still depends on observed telemetry. This distinction matters for Payment, where the report offers a troubleshooting step and leaves the hypothesis unset.

Retrieval-augmented generation adds a generation step that supplies retrieved sections to a language model. Hybrid retrieval also adds another retrieval signal, usually vector similarity, so queries can find conceptually related passages with different wording.

## Search and ranking strategies

Search determines which sections qualify. Ranking determines which qualifying sections appear first. For example, if the query is about high CPU on the Ad service, a search might find several sections that mention CPU. The ranker decides whether “Investigate sustained Ad CPU” should appear above a section that mentions CPU in passing.

| Strategy | How it finds or ranks sections | Where it fits in OpsPilot |
|---|---|---|
| Substring search | Looks for a sequence of characters, such as `cpu`. A caller can add rules like preferring a heading match. | A simple alternative for a few files. Useful for understanding what a full-text index adds. |
| SQLite FTS5 and BM25 | FTS5 looks up normalized terms in an inverted index, which maps each term to the sections that contain it. BM25 scores the matches using term frequency, term rarity across sections, and section length. | The default keyword search in [`keyword_order()`](../opspilot/evidence/runbooks.py#L30). |
| PostgreSQL full-text search | Converts text to normalized terms in a `tsvector`. A GIN index helps identify rows matching a `tsquery`. `ts_rank` considers frequency and field weights, and `ts_rank_cd` also considers proximity. | An alternative keyword search if runbooks are stored in PostgreSQL. The current project uses SQLite for keywords, including when pgvector supplies semantic results. [PostgreSQL ranking](https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-RANKING) · [GIN indexes](https://www.postgresql.org/docs/current/textsearch-indexes.html) |
| Semantic search | Converts the query and sections into vectors and compares them by cosine similarity or distance. It can associate “processor saturation” with “high CPU” even when the words differ. | The optional second ranking in [`semantic_order()`](../opspilot/evidence/embeddings.py#L32) or [`pgvector_order()`](../opspilot/evidence/vector_store.py#L13). |
| Hybrid search | Runs keyword and semantic retrieval and combines their rankings. | [`retrieve_runbooks()`](../opspilot/evidence/runbooks.py#L45) combines both when `OPSPILOT_RUNBOOK_SEARCH=hybrid`. See [how the two rankings combine](20-hybrid-runbook-search.md#how-opspilot-combines-the-rankings). |

For `ad-high-cpu`, `retrieve_runbooks()` builds the query `"ad" AND ("cpu" OR "high")`. In SQLite, `MATCH` requires the service term and at least one symptom term. Then `bm25(chunks, 0, 0, 3, 1)` gives one occurrence in the heading three times the weight of one in the excerpt when counting matching terms. The final BM25 score also depends on term rarity and section length. SQLite puts better BM25 matches first in ascending order. The query keeps up to five keyword results, and retrieval ultimately returns one section. [SQLite FTS5](https://www.sqlite.org/fts5.html#the_bm25_function)

## Practice

Run `uv run opspilot replay payment-failure` and inspect the search query and selected heading. Compare it with the recovery section and explain which words favor the result. Then run `uv run opspilot eval` to check whether every scenario still cites its expected section.
