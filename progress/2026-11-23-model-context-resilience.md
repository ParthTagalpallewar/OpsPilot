# 2026-11-23 · Model context protection and provider retries

The optional Claude call now sends allowlisted numeric summaries and structured change timing, and includes runbook text only if its exact bundled revision is approved. Evidence identifiers are replaced with request-local aliases and restored after validation. The original evidence remains in the local report.

Added one bounded retry for transient errors and jitter between attempts. The provider fallback preserves the baseline report. Mocked tests verify context exclusion, citation mapping, retry limits, and abstention. Live Claude behavior and semantic scoring remain unverified.

See the [model context and retries lesson](../Concepts/32-model-context-and-retries.md).
