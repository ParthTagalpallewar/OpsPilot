# 2026-11-22 · Live Jaeger verification and log correlation

Verified the Payment trace capture against an isolated Jaeger 2.21 container over real HTTP. The first request exposed a format mismatch. Jaeger wraps OTLP data under a result field, so the parser now accepts that envelope and bare exports. The corrected CLI preserved the 20 ms error span and Checkout parent from the synthetic trace.

Payment replay now joins structured warning records to failed spans when both normalized IDs match. The report cites both evidence records and lists the matching log lines. The test covers a warning on a different span in the same trace. The historical Payment warning lacks those IDs, so its replay remains unchanged.

This verifies Jaeger transport and correlation mechanics with controlled data. A captured incident from the OpenTelemetry Demo still needs a matched log and trace.

See the [distributed traces lesson](../Concepts/10-distributed-traces.md).
