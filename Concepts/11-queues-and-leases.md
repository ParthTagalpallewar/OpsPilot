# Durable queues and worker leases

A request with `queued: true` returns HTTP 202 and an investigation ID. SQLite stores the incident and job in one transaction. Both rows become visible together, so a worker can find the job even if the API exits immediately after responding.

A worker uses a short database transaction to claim a job, move the report to `running`, and set a 60-second lease. It processes the capture outside that transaction. If the worker stops before saving its result, another worker can claim the job once the lease expires.

A lease helps with recovery, but a slow worker can resume after a new worker has claimed the job. OpsPilot gives each claim a token. Saving the report and removing the job happen in one transaction, and that transaction checks the token first. This allows repeated execution of the read-only replay while keeping a stale worker from overwriting the newer result.

A lease alone can retry forever. If a job makes its worker fail every time, each new claim fails the same way and the investigation stays `running`. OpsPilot counts claims in `replay_jobs.attempts`, like a message queue's delivery count. After three claims that never finished, the next worker removes the job and marks the investigation `failed`, which also ends its event stream.

The worker loop survives errors outside a replay, such as a locked database: it logs the traceback, waits a few seconds, and continues, leaving the claimed job to its lease. On SIGTERM it finishes the current job and exits. In a container the worker is PID 1, which ignores SIGTERM unless the program installs a handler, so without one every shutdown waits out the grace period and ends in SIGKILL.

## Practice

Submit a queued incident using the API docs. Use the response's `Location` to check the queued status. Run the worker with `--once` and fetch the same location again. Compare this with an HTTP 201 synchronous replay. Then start the worker without `--once`, send it `kill -TERM`, and check that it exits with status 0.
