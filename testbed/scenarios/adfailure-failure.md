# Scenario: High CPU in the Ad Service

## Setup
- Flag: `adHighCpu`
- Variant: `on` (confirm on http://localhost:8080/feature)
- Affected service: `ad`
- Time flipped: (IST, UTC+5:30): about 19:47:41
- Load generator running: yes (/loadgen/)
- Precondition: `paymentFailure` is `off` (0 "Payment request failed" in the last 2 minutes)

## Baseline (before the fault)
Taken with `docker stats ad --no-stream`, time: <HH:MM:SS>

| Container | CPU % | Memory usage / limit | Mem % | Net I/O | PIDs |
|---|---|---|---|---|---|
| ad (cf4592353200) | 1.31% | 233.4 MiB / 300 MiB | 77.81% | 2.34 MB / 13.6 MB | 51 |

Note: memory is already near 78% of the limit before any fault. Watch for restarts or OOM kills.

## During the fault
Readings every 30 seconds with `docker stats ad --no-stream`:

| Time | Seconds since flip | CPU % | Memory | Notes |
|---|---|---|---|---|
| <time> | 30 | <> | <> | |
| <time> | 60 | <> | <> | |
| <time> | 90 | <> | <> | |
| <time> | 120 | <> | <> | |

- Peak CPU: <value>
- Baseline vs peak: 1.31% -> <peak>%
- Container restarted or OOM-killed: <yes/no, from `docker ps`>

## Timeline
- Flag flipped: <time>
- First visible symptom (CPU clearly above baseline): <time>, about <N> seconds after the flip
- Reverted (`adHighCpu` set to `off`): <time>
- CPU back near baseline: <time>

## Evidence
| Signal | Where | What I saw |
|---|---|---|
| Metrics | `docker stats ad` | CPU rose from 1.31% to <peak>% |
| Metrics | Grafana, Demo Dashboard, service `ad`, Application Metrics | <CPU panel present or empty> |
| Metrics | Grafana, Spanmetrics, p95 latency for `ad` and `frontend` | <before -> during> |
| Traces | Jaeger, service `ad`, operation `GetAds` | <typical duration -> duration during fault> |
| Logs | `docker logs ad --since 10m` | <nothing unusual / what appeared> |

## Red herrings and gotchas
- Logs are likely empty. The evidence is in metrics and traces, not error logs.
- The Linux dashboard shows the whole Docker VM, not per-service CPU. Use `docker stats` for `ad`.
- `jaeger` (~60% CPU) and `opensearch` (~94% memory) are noisy neighbors. Compare `ad` against its own baseline.
- Grafana's Application Metrics CPU panel may not cover `ad`.

## Root cause
`ad` service, injected through the `adHighCpu` flag. Symptoms: high CPU on `ad`, slower `GetAds` spans, and possible latency impact on `frontend`.

## Revert
Set `adHighCpu` to `off`, wait 2 to 3 minutes, and confirm `docker stats ad` is back near baseline.

x- Post-revert reading: CPU 0.33%, memory 251.9 MiB (83.98%). CPU recovered fully, memory did not return to baseline.