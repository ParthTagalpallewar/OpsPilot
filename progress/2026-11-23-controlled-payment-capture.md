# 2026-11-23 · Controlled Payment capture

Ran the real OpenTelemetry Demo Payment, flagd, and collector images in an isolated temporary Compose project. A direct instrumented gRPC client sent six synthetic charges with the fault disabled and six with the 100% fault enabled. The original demo checkout and flags file were untouched.

Saved a reduced capture with six matching OTLP warnings and failed server spans, plus measured client counts of 0/6 baseline failures and 6/6 fault failures. Payment replay now validates count consistency and cites each observed batch rate. The three golden scenarios remain unchanged.

The test called Payment directly. A full Checkout-to-Payment capture and live alert-driven collection remain pending.

See the [controlled experiments lesson](../Concepts/29-controlled-fault-experiments.md).
