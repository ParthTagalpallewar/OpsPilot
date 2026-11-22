# Runbook retrieval and BM25

A runbook records troubleshooting steps. OpsPilot splits each Markdown document at its level-two headings so an investigation can cite a specific section. The [Payment runbook](../testbed/runbooks/payment-failures.md) contains one section for diagnosis and another for checking recovery.

The graph builds a query from the service, scenario words, and the first captured warning message when available. SQLite FTS5 stems related words such as “failure” and “failures.” BM25 ranks matching sections using how often terms appear in a section, how common they are across the collection, and how long each section is. OpsPilot gives title matches more weight and returns one ranked section.

The report's guidance cites the section by evidence ID. The record includes its heading, line, excerpt, and search query. A match can tell an operator what to check. Confirmation of the cause still depends on observed telemetry. This distinction matters for Payment, where the report offers a troubleshooting step and leaves the hypothesis unset.

Retrieval-augmented generation adds a generation step that supplies retrieved sections to a language model. Hybrid retrieval also adds another retrieval signal, usually vector similarity, so queries can find conceptually related passages with different wording.

## Practice

Run `uv run opspilot replay payment-failure` and inspect the search query and selected heading. Compare it with the recovery section and explain which words favor the result. Then run `uv run opspilot eval` to check whether every scenario still cites its expected section.
