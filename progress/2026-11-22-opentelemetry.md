# 2026-11-22 · OpsPilot tracing

Added optional OpenTelemetry tracing for incident intake, worker execution and the replay graph. The SQLite queue persists W3C trace context so a separate worker process can continue the trace. Console export is useful for local inspection. OTLP HTTP export can send the same spans to a collector.

The tracing spans exclude raw payloads and exception messages. Langfuse experiments, metrics, and collector deployment verification remain pending.

See the [instrumentation lesson](../Concepts/13-opentelemetry-instrumentation.md).

Verified console output from separate intake and worker processes. The worker inherited the intake trace ID, and replay and runbook spans shared the same trace. A sentinel incident title and description did not appear in the spans. All twelve tests and three replay evaluations passed.
