# Controlled fault experiments

To measure a change, send comparable requests before and after introducing the fault. Record the total attempts and failures at the client, which observes every result in the batch. Sampled traces and warning counts help explain failures. Use the observed request totals as the denominator.

The controlled Payment capture recorded six successful gRPC calls with the failure flag off and six failed calls with it set to 100%. The warning's trace ID and span ID tie it to a specific failed server operation. The parent belongs to the instrumented test client, which shows where the request originated.

## Practice

Replay the [controlled capture](../testbed/captures/payment-controlled/README.md). Follow one correlation observation to the warning and span evidence. Explain why the observed 100% batch failure rate applies to the test rather than all traffic to Payment.

## Observe failure propagation

The [Checkout capture](../testbed/captures/checkout-payment/README.md) adds the upstream service. Follow the chain from a Checkout client call to the Checkout span, then to Payment. An HTTP or gRPC failure measured at the caller tells you what users of that service experienced. The traced downstream operation helps explain where the failure originated.
