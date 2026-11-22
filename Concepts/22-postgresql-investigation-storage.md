# Shared PostgreSQL state and transaction locks

The local SQLite mode keeps incidents, jobs, events, and approval history in one file. The PostgreSQL mode stores the same investigation data behind a network connection. An API and separate workers can point at the same database and see the same state.

A PostgreSQL advisory transaction lock serializes short writes for this implementation. A worker holds it while claiming a job, then releases it before running the investigation. It acquires the lock again to publish events and commit results. This preserves the claim-token and approval checks across processes while allowing different workers to analyze different jobs concurrently.

The same lock keeps event IDs in commit order, so advancing a cursor does not skip a transition from an earlier write. Reads use a repeatable snapshot when loading investigation state and its approval history. At larger scale, narrower row locks and partitioned event streams can reduce contention. Measure how long writes wait before changing the concurrency design.

## Practice

Start the development PostgreSQL service and run the API and worker using the README. Submit a queued incident. Stop and restart the API and confirm that the same report and approval history are available from PostgreSQL.
