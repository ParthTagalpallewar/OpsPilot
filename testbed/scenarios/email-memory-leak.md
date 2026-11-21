# Scenario: Memory Leak in the Email Service

## Setup
- Flag: `emailMemoryLeak`
- Variants tried, in order: `100x`, `1000x`, `10000x`
- Affected service: `email` (memory limit 100 MiB)
- Load generator running: yes
- Precondition: `paymentFailure` and `adHighCpu` were `off`
- Raw data: `email-stats-baseline.csv`, `email-stats-fault.csv` (`docker stats email --no-stream`, one reading about every 31 s; the `variant` column marks the active variant)

## Baseline (before the fault)
Window: 2026-11-21 15:54:56Z to 16:01:11Z, 13 readings.

| Metric | Min | Average | Max |
|---|---|---|---|
| Memory | 61.21 MiB | 61.61 MiB | 62.30 MiB |
| Memory % of 100 MiB limit | 61.2% | 61.6% | 62.3% |
| CPU % | 0.03% | 1.51% | 5.22% |
| PIDs | 22 | | 23 |

Memory is flat (trend about +0.03 MiB/min). CPU spikes of 4 to 5% appear when orders complete, so they are normal.

## Fault timeline (UTC)

| Variant | First reading | Last reading | Readings | Switch time (known range) |
|---|---|---|---|---|
| `100x` | 16:02:27 | 16:11:26 | 18 | flag turned on between 16:01:11 and 16:02:27 |
| `1000x` | 16:12:26 | 16:16:35 | 9 | switched between 16:11:26 and 16:12:26 |
| `10000x` | 16:17:29 | 16:20:04 | 6 | switched between 16:16:35 and 16:17:29 |

The exact click times were not recorded. Capture was stopped and restarted at each switch, so there are gaps of about 1 minute at each switch.

The 16:02:27 reading was logged to the baseline file by mistake. It is moved to the fault file here. It still shows 61.44 MiB, so no effect was visible yet.

## Results by variant

| Variant | Memory range | Average | Peak | Trend (MiB/min, rough) |
|---|---|---|---|---|
| Baseline | 61.2 to 62.3 MiB | 61.6 MiB | 62.3 MiB | +0.03 |
| `100x` | 61.4 to 73.8 MiB | 68.6 MiB | 73.83 MiB (73.8%) | +1.2 |
| `1000x` | 75.1 to 92.8 MiB | 86.0 MiB | 92.83 MiB (92.8%) | +3.0 |
| `10000x` | 79.5 to 89.7 MiB | 84.2 MiB | 89.65 MiB (89.7%) | +3.0, driven by one jump at 16:19:33 |

Overall: memory rose from 61.6 MiB (baseline average) to 89.65 MiB at the last reading, about +28 MiB in 17.6 minutes, roughly 1.6 MiB/min. Highest reading: 92.83 MiB at 16:14:00Z.

## What the data shows
- **Memory grows in a sawtooth, not a smooth line.** It climbs, then drops (for example 73.83 -> 67.61 MiB at 16:06:45, and 92.83 -> 90.04 -> 88.85 MiB after 16:14:00). Garbage collection reclaims part of it, so growth is uneven.
- **Higher variants did not scale linearly.** `1000x` and `10000x` both settle around 85 to 90 MiB, close to the 100 MiB limit. `10000x` was not 10 times worse than `1000x`.
- **Peaks are sudden.** The jumps (66.3 -> 73.8 MiB at 16:06:14, 78.6 -> 92.8 MiB at 16:14:00, 79.5 -> 89.2 MiB at 16:19:33) line up with PIDs rising or CPU spikes of 2 to 6%, which fits an order completing and a large email body being built.
- **No OOM kill seen in the readings.** The peak was 92.83 MiB. Confirm with `docker inspect`.
- **CPU is not the signal.** It stayed in the baseline range (spikes up to 6.15%).

## Evidence
| Signal | Where | What I saw |
|---|---|---|
| Metrics | `docker stats email` | Memory rose from about 61.6 MiB to 89 to 93 MiB, with a sawtooth pattern |
| Metrics | Grafana, `email` memory | <present or empty> |
| Traces | Jaeger, `email` spans | <duration change, if any> |
| Logs | `docker logs email --since 30m` | <nothing unusual / what appeared> |
| Container state | `docker inspect email` | OOMKilled=<> Restarts=<> |

## Red herrings and gotchas
- Memory is not a straight line, and it can drop. An agent that only checks "is memory growing in every sample" will miss it. Compare the average or peak against baseline instead.
- A high variant raises the level, but not by the variant's multiplier.
- CPU spikes of 4 to 6% are normal order activity, not evidence of the fault.
- `email` only grows when orders complete, so low traffic hides the symptom.
- The baseline of `email` was 58.3 MiB in the first `docker stats` and 61.6 MiB here, so use this scenario's own baseline.

## Root cause
`email` service, injected through the `emailMemoryLeak` flag. The variant controls how much each confirmation email body is padded. Symptom: memory rising toward the 100 MiB limit, with no matching errors.

## Revert (still to do)
1. Set `emailMemoryLeak` to `off` on `/feature`. Note the UTC time: <time>
2. `docker restart email`
3. Confirm memory is back near 61 MiB: `docker stats email --no-stream`
4. `docker inspect email --format 'OOMKilled={{.State.OOMKilled}} Restarts={{.RestartCount}}'`
