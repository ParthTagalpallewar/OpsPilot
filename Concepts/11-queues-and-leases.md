# Durable queues and worker leases

A request with `queued: true` returns HTTP 202 and an investigation ID. SQLite stores the incident and job in one transaction. Both rows become visible together, so a worker can find the job even if the API exits immediately after responding.

A worker uses a short database transaction to claim a job, move the report to `running`, and set a 60-second lease. It processes the capture outside that transaction. If the worker stops before saving its result, another worker can claim the job once the lease expires.

A lease helps with recovery, but a slow worker can resume after a new worker has claimed the job. OpsPilot gives each claim a token. Saving the report and removing the job happen in one transaction, and that transaction checks the token first. This allows repeated execution of the read-only replay while keeping a stale worker from overwriting the newer result.

## Practice

Submit a queued incident using the API docs. Use the response's `Location` to check the queued status. Run the worker with `--once` and fetch the same location again. Compare this with an HTTP 201 synchronous replay.
