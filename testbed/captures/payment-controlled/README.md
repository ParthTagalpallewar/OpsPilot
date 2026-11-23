# Controlled Payment incident capture

Captured on November 23, 2026, from an isolated local stack using the cached OpenTelemetry Demo Payment image, flagd v0.16.0, and OpenTelemetry Collector Contrib v0.160.0. An instrumented gRPC test client sent six synthetic charge requests with `paymentFailure=off` and six more after restarting Payment and flagd with the flag set to `100%`. The script recorded response status counts for each batch. All six baseline requests succeeded and all six fault requests returned gRPC status 2.

The collector's file exporter recorded logs and traces. The fixture keeps the six matching warnings and their traces, retaining service names, timestamps, identifiers, operation names, and status codes. Other span and log attributes were removed. `payment-logs.jsonl` was generated from the reduced OTLP logs with the OpsPilot CLI.

The direct caller was `payment-capture-client`. The Checkout service was outside this experiment. The percentages describe these controlled batches.

```sh
uv run opspilot replay payment-failure --captures testbed/captures/payment-controlled
```
