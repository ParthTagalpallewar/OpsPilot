# 2026-11-23 · OpsPilot operational metrics

Added optional OpenTelemetry metrics for available queue depth, committed job outcomes, worker processing duration, approval wait, and provider-reported token usage. API queue measurements come from persisted lease state. Outcome timing and approval metrics record after finalization, so a stale worker or repeated decision does not double-count a result.

Verified gauge transitions and counters with the SDK's in-memory reader, including a repeated approval. Console or OTLP metric export is opt-in. Dashboard rules and latency measurements under representative load remain pending.

See the [OpenTelemetry lesson](../Concepts/13-opentelemetry-instrumentation.md).
