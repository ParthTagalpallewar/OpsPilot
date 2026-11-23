# 2026-11-23 · Payment failure-rate evidence for live alerts

Added optional Prometheus sampling to live Payment alerts. The worker reads a configured percentage series across alert-relative windows and freezes the responses beside the trace. Replay cites each mean sampled failure rate. Failed metric collection is recorded as partial coverage and the frozen trace remains available.

Verified the worker capture path with controlled responses and the measured trace fixture. These are means of sampled rates. Exact live request totals and a combined end-to-end test against the demo's actual request counters remain pending.

See the [alert-driven evidence lesson](../Concepts/30-alert-driven-evidence.md).
