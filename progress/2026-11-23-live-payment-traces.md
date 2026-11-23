# 2026-11-23 · Jaeger collection from Payment alerts

Extended live Alertmanager intake to accept Payment alerts with a valid hex trace ID annotation and a configured Jaeger destination. The worker fetches the nominated trace, validates a failed Payment span, publishes the frozen response, and streams a capture step. It reuses an existing snapshot after reclaim.

The live Payment path requires the trace ID in the alert. Automatic trace discovery, log retrieval, and aggregate request counts remain pending for these alerts.

See the [alert-driven evidence lesson](../Concepts/30-alert-driven-evidence.md).

Verified with Jaeger 2.21 and a separate worker process. A measured Checkout-to-Payment trace was loaded into the temporary server. The worker retrieved it over HTTP and the resulting report reproduced exactly offline. Alerts without a trace ID were ignored. All thirty-two tests and seven evaluation cases passed.
