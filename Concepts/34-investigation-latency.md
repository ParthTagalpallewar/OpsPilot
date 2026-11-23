# Measuring investigation latency

The local benchmark starts its timer immediately before the HTTP request that queues an investigation. It stops when the client receives the completed event. This includes API submission, queue wait, worker processing, database writes, and event delivery. Human review happens later.

The worker duration histogram starts after a job is claimed and ends after its result is committed. The time it measures excludes queue wait and delivery. Comparing it with the client measurement helps locate delays. A slow client result alongside a short worker duration can point to the queue or event stream.

The benchmark warms up once, then rotates through the three frozen scenarios at a fixed concurrency. The median describes the middle result. The nearest-rank p95 describes the slow end of the observed sample. With 30 runs, a few changes can move that percentile considerably. A result from this local replay workload does not establish performance for live collection or model calls.

## Practice

Run the benchmark at concurrency one and five against the same deployment. Compare the p95, inspect the queue depth, and explain how queuing and SSE polling could affect the client measurement.
