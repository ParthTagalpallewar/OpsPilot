# 2026-11-22 · Payment trace replay

Payment replay now accepts a saved OTLP JSON export as `payment-traces.json` alongside the captured log. Each failed Payment span becomes cited evidence with its operation, duration, source IDs, and direct parent service when available. The loader rejects malformed exports, negative durations, and duplicate span IDs within a trace.

The workspace contains no measured Payment trace export. The test uses synthetic spans to exercise the complete replay graph. The standard Payment case remains backed by the saved warning and leaves the cause unresolved. Live trace collection and cross-signal correlation still need real captures.

See the [distributed traces lesson](../Concepts/10-distributed-traces.md).
