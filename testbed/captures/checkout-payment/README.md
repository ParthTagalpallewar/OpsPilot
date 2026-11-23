# Checkout-to-Payment fault capture

Captured on November 23, 2026, from isolated OpenTelemetry Demo Checkout, Payment, and their dependencies. An instrumented gRPC test client sent six synthetic Checkout orders with `paymentFailure=off`. It sent another six after flagd and Payment restarted with the flag set to `100%`.

| Checkout request batch | UTC start | Failed | Client result |
|---|---|---:|---|
| Baseline | 02:19:05.903 | 0 of 6 | All completed |
| Fault | 02:19:21.350 | 6 of 6 | All returned gRPC `INTERNAL` while charging the card |

Each fault warning shares both identifiers with a failed Payment server span. Each Payment span has a recorded Checkout parent. The reduced export keeps the spans on those ancestor paths and strips request attributes, exception stack traces, and unrelated records. Raw PII telemetry was disabled in the test stack. The percentages apply to the test batches.

```sh
uv run opspilot replay payment-failure --captures testbed/captures/checkout-payment
```
