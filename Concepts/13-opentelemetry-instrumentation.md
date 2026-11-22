# Tracing OpsPilot with OpenTelemetry

A span records an operation's start, end, name, and attributes. OpsPilot creates spans for incident intake, worker execution, replay, evidence collection, runbook retrieval, and report validation. The replay spans show where time went inside the investigation.

The API and worker run in different processes. The API writes W3C trace context into the queued job's transaction. The worker restores that context before it starts its span. The trace ID stays the same and the worker's parent span ID points to incident intake. The job's trace context is removed when the result is committed.

Run `OPSPILOT_TRACING=console uv run opspilot replay ad-high-cpu` to print spans to standard error alongside the JSON report on standard output. Set `OPSPILOT_TRACING=otlp` and `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` to send spans to a collector over OTLP HTTP.

The spans record operation names, scenario, worker investigation ID, and outcome. Payloads, prompts, and raw exception messages stay out of the span data.

## Practice

Compare the IDs in the replay span and its runbook retrieval span. Then enable tracing in the API and worker, queue a replay, and look for a worker span whose parent ID matches the intake span from the API.
