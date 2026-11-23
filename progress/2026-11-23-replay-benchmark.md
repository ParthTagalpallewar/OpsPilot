# 2026-11-23 · Investigation latency benchmark

Added an HTTP benchmark that submits queued investigations and measures time to the terminal SSE event. It excludes approval wait and rotates through the frozen Ad, Email, and Payment scenarios. Each run used one warm-up request, 30 measured jobs, five concurrent clients, and one worker on the same local host.

| Backend | Completed | p50 | p95 | Max |
|---|---:|---:|---:|---:|
| SQLite | 30/30 | 1.025 s | 2.030 s | 2.032 s |
| PostgreSQL + Redis | 30/30 | 1.094 s | 1.161 s | 1.174 s |

The queue-to-approval HTTP smoke test passed for both newly built Compose images. These measurements cover deterministic replay and local event delivery. Live telemetry and provider latency remain unmeasured in this workload.

See the [investigation latency lesson](../Concepts/34-investigation-latency.md).
