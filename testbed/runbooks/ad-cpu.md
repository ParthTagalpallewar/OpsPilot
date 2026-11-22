# Ad service operations

## Investigate sustained Ad CPU
Compare Ad CPU with its baseline while checking request volume and GetAds latency. Inspect slow traces for time spent in the Ad service. Review feature flag and deployment changes near the start of the CPU increase.

## Verify recovery after mitigation
Repeat the CPU and latency measurements after the operator applies the mitigation. Use comparable traffic windows and record the recovery time.
