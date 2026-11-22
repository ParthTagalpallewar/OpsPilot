# Redis wake-up signals and durable jobs

The API commits the job to SQLite or PostgreSQL before sending a Redis wake-up hint. A blocked worker receives the hint and asks the database for the next job. The database decides who owns it through the lease and claim token.

Redis carries a short-lived signal. The list is capped and expires after idle time. If an API process exits between commit and notification, the hint can be lost while the job remains available. The worker's blocking Redis read times out and it checks the database again. If Redis is unavailable, the worker falls back to polling.

This pattern makes Redis useful for responsiveness while giving the database responsibility for recovery. Compare it with systems that need a transactional outbox because every individual message must reach a downstream consumer.

## Practice

Start a worker with Redis enabled and submit a replay. Then stop a disposable Redis instance and submit another replay. Use the event stream to confirm both jobs complete.
