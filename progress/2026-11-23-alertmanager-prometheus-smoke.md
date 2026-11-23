# 2026-11-23 · Alertmanager and live Prometheus smoke test

Submitted a synthetic firing alert without a trace ID to isolated Alertmanager
0.31.1 through its alerts API. Alertmanager delivered the authenticated webhook,
OpsPilot returned HTTP 202, and the worker processed exactly one investigation.
The worker queried Payment server-span counters from the running
OpenTelemetry Demo's Prometheus and froze both windows. The report cited
0.00% mean sampled failure rates for both windows and recorded partial
coverage because Jaeger found no eligible failed span.

The smoke test verified Alertmanager delivery, queue processing, and live
Prometheus evidence capture. The alert was seeded directly into Alertmanager.
A Prometheus rule firing during an induced Payment failure, with matching
live trace and log evidence, remains unverified. The temporary Alertmanager,
API process, and capture database were removed.
