# 2026-11-22 · Live capture verification and Jaeger intake

Verified the Prometheus CLI against a temporary Prometheus container over real HTTP. A controlled PromQL expression produced five samples per window and known means of 2% and 90%. Offline replay reproduced both means. The test verifies the transport and parsing through a real Prometheus server. Actual OpenTelemetry Demo resource data remains unverified because the demo stack was stopped.

Added a Jaeger v3 capture command for a known Payment trace ID. It validates the OTLP JSON and the presence of a failed Payment span before freezing the response. Payment replay supports a trace by itself as well as combined log and trace captures. The Jaeger test uses a mocked HTTP response. Live Jaeger delivery remains unverified.

See the [distributed traces lesson](../Concepts/10-distributed-traces.md) and [Prometheus lesson](../Concepts/18-prometheus-range-queries.md).
