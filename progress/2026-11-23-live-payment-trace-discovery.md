# 2026-11-23 · Payment trace discovery

Live Payment alerts can omit the trace ID. The worker searches Jaeger's v3
API in the ten minutes before the alert, checks for failed Payment spans in
that window, and freezes the selected trace. Explicit trace IDs still work.
Log correlation follows the saved trace ID. When Jaeger has no match or is
unavailable, captured Prometheus evidence can still produce a partial report.

Verification uses the webhook, queue, and worker with recorded Checkout
telemetry and a controlled Jaeger HTTP response. The running demo's Jaeger
2.21 endpoint also returned search responses at the configured /jaeger/ui
prefix. The live search returned no eligible failed span during verification.

A separate Jaeger 2.21 container accepted the scrubbed Checkout trace
fixture over OTLP. The worker discovered a failed trace from an alert
without a trace ID, linked its warning by trace and span ID, and completed
the investigation. This exercised the real Jaeger search and trace lookup
with replayed telemetry. The temporary container and database were removed.

Ruff, all 36 tests, and all seven replay evaluation cases passed. A newly
fired Alertmanager notification with live Prometheus counters still needs
end-to-end verification.
