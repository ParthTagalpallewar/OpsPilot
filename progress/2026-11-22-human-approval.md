# 2026-11-22 · Local human approval

Added dry-run plans for replay reports with hypotheses. The approval endpoint supports approve, reject, and edit. Reviews match the active plan ID and content hash, and expired plans return a conflict. Edits issue a new reviewable plan. SQLite stores a sequence of review events and serializes updates so a plan receives at most one decision. An immediate retry of an identical decision returns the saved result.

This is the local review flow. Shared reviewer identity, PostgreSQL audit storage, and resuming a LangGraph checkpoint are pending.

See the [human review lesson](../Concepts/06-human-approval.md) and the [incident intake milestone](2026-11-22-incident-intake.md).

Verified edits, stale-plan conflicts, expiry, invalid edit requests, rejection, concurrent decisions, retry behavior, and persistence across store instances. Ruff, six tests, and all three replay evaluations passed.
