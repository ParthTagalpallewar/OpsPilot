# Distributed traces and error spans

A trace groups spans from one request using a trace ID. Each span has its own span ID and may include the ID of its parent. OpsPilot looks up a parent using both IDs. This keeps a span from a different trace out of the relationship.

A saved OTLP JSON export groups spans by resource and instrumentation scope. The resource's `service.name` attribute identifies the service. The replay selects Payment spans with an explicit error status and converts elapsed nanoseconds to milliseconds by dividing by 1,000,000.

A Payment error span with a direct Checkout parent tells you which instrumented operations were related. To determine whether a flag caused it, compare multiple traces with request outcomes and independently recorded change times. Sampling and partial exports can omit spans, including a parent.

## Practice

Read [the trace replay test](../tests/evidence/test_traces.py) and predict the duration shown for the `Charge` span. Change the parent's trace ID in the test data and check how that affects parent resolution.

See the [Jaeger trace retrieval API documentation](https://www.jaegertracing.io/docs/2.23/architecture/apis/).

## Capture a trace from Jaeger

Choose an existing trace ID in your local Jaeger instance. OpsPilot's capture command calls the Jaeger v3 trace endpoint and freezes the OTLP JSON response. It requires the trace to contain a failed Payment span. The capture can replay by itself or alongside a log capture. When both are present, the report shows both evidence sources. A confirmed log-to-span link requires a trace or span ID in the log record.

## Link a warning to a failed span

A structured Payment log can include optional hexadecimal `trace_id` and `span_id` fields. OpsPilot normalizes case and joins the pair against the failed spans. The observation cites the log cluster and span and identifies the exact matching source lines. Sharing only the trace ID means two records relate to the same request, while the span ID identifies the particular operation.
