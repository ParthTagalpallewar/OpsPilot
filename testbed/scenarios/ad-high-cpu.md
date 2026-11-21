# Scenario: High CPU in the Ad Service

## Setup
- Flag: `adHighCpu`
- Variant: `on` (confirm on http://localhost:8080/feature)
- Affected service: `ad`
- Time flipped: <HH:MM:SS UTC, between 14:30:19Z and 14:31:25Z>
- Load generator running: yes
- Precondition: `paymentFailure` was `off`
- Raw data: `ad-stats-baseline.csv`, `ad-stats-fault.csv` (collected with `docker stats ad --no-stream` every ~31 s)

## Baseline (before the fault)
Window: 2026-11-21 14:20:55Z to 14:30:19Z, 19 readings.

| Metric | Min | Average | Max |
|---|---|---|---|
| CPU % | 0.11% | 0.74% | 2.17% |
| Memory | 233.5 MiB | 233.7 MiB | 234.0 MiB |
| Memory % of 300 MiB limit | 77.8% | 77.9% | 78.0% |
| PIDs | 51 | | 53 |

Normal CPU spikes reach about 2%. Memory is flat. `ad` already sits near 78% of its memory limit.

## During the fault
Window: 2026-11-21 14:31:25Z to 15:03:09Z, 62 readings (about 32 minutes).

| Metric | Min | Average | Max |
|---|---|---|---|
| CPU % | 386.87% | 398.0% | 402.70% |
| Memory | 234.3 MiB | 242.9 MiB | 244.4 MiB |
| Memory % of 300 MiB limit | 78.1% | 81.0% | 81.5% |
| PIDs | 55 | | 57 |

Key readings:
- First reading in the fault window (14:31:25Z): 397.86% CPU. The flag was already effective by then.
- CPU stayed at about 400% for the whole window, with no recovery.
- Memory stepped up about 7 MiB at 14:32:29Z (235.0 -> 242.4 MiB), then stayed near 243 MiB. This is a small increase, not a leak.
- PIDs rose from 51-53 to 55-57.
- Container restarted or OOM-killed: <yes/no, check `docker ps` and `docker inspect ad --format '{{.State.OOMKilled}}'`>

## Baseline vs fault

| Metric | Baseline avg | Fault avg | Change |
|---|---|---|---|
| CPU % | 0.74% | 398.0% | about 540x |
| Memory | 233.7 MiB | 242.9 MiB | +9.2 MiB (+3.9%) |
| PIDs | 51-53 | 55-57 | +4 |

CPU near 400% means `ad` is saturating about 4 CPU cores. Docker reports CPU per core, so 100% equals one core.

## Timeline (UTC)
- 14:30:19 Last baseline reading (0.32% CPU)
- <flip time> `adHighCpu` set to `on`
- 14:31:25 First fault reading (397.86% CPU), within about 66 s of the last baseline reading
- 15:03:09 Last fault reading, CPU still about 397%
- <revert time> `adHighCpu` set to `off`
- <recovery time> CPU back to baseline (under 3%)

## Evidence
| Signal | Where | What I saw |
|---|---|---|
| Metrics | `docker stats ad` | CPU rose from 0.74% (avg) to about 398% and stayed there |
| Metrics | Grafana, Demo Dashboard, service `ad`, Application Metrics | <CPU panel present or empty> |
| Metrics | Grafana, Spanmetrics, p95 latency for `ad` and `frontend` | <before -> during> |
| Traces | Jaeger, service `ad`, operation `GetAds` | <typical duration -> duration during fault> |
| Logs | `docker logs ad --since 30m` | <nothing unusual / what appeared> |

## Red herrings and gotchas
- Logs are likely empty. The evidence is in metrics and traces, not error logs.
- Memory rose only about 4%, so memory is not the signal for this fault. CPU is.
- The Linux dashboard shows the whole Docker VM, not per-service CPU. Use `docker stats` for `ad`.
- `jaeger` (~60% CPU) and `opensearch` (~94% memory) are noisy neighbors. Compare `ad` against its own baseline.
- Grafana's Application Metrics CPU panel may not cover `ad`.
- A CPU burn of about 400% on a laptop can slow other containers, which can add latency to unrelated services.

## Root cause
`ad` service, injected through the `adHighCpu` flag. Symptoms: sustained CPU near 400% on `ad`, slower `GetAds` spans, and possible latency impact on `frontend`.

## Revert
Set `adHighCpu` to `off`, wait 2 to 3 minutes, and confirm `docker stats ad` is back under about 3%. Record the revert and recovery times above.
