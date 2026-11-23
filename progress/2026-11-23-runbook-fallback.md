# 2026-11-23 · Runbook retrieval fallback

Hybrid retrieval now preserves keyword guidance when embeddings or pgvector are unavailable. If keyword search fails while the vector path succeeds, the report can cite semantic guidance. Unreadable runbook files are skipped individually. Source issues are attached to the report without changing the telemetry findings.

A mocked pgvector failure verified that the graph still returns the cited Ad runbook and the original leading hypothesis while marking the report partial. Fully unavailable live telemetry providers remain a separate failure mode.

See the [partial evidence lesson](../Concepts/33-partial-evidence.md).
