# 2026-11-23 · Checkout-to-Payment incident capture

Ran Checkout and its dependencies in an isolated project so the existing demo containers and flags were unaffected. Six synthetic Checkout orders succeeded with the Payment failure flag off. Six returned gRPC INTERNAL during the 100% fault. All six Payment warnings matched a failed server span with a direct Checkout parent.

Saved the reduced logs, traces, and client counters as a separate replay fixture. Payment replay now identifies where the client measured the request counts and exposes the parent operation in trace evidence. The golden fixtures remain available. Alert-driven live collection remains pending.

See the [Checkout capture](../testbed/captures/checkout-payment/README.md) and [controlled experiments lesson](../Concepts/29-controlled-fault-experiments.md).
