# Scenario: Memory Leak in the Email Service

## Setup
- Flag: `emailMemoryLeak`
- Variants tried, in order: `100x`, `1000x`, `10000x`
- Affected service: `email` (Ruby/Sinatra on Puma, memory limit 100 MiB)
- Load generator running: yes
- Precondition: `paymentFailure` and `adHighCpu` were `off`
- Raw data: `email-stats-baseline.csv`, `email-stats-fault.csv` (`docker stats email --no-stream`, about one reading every 31 s; the `variant` column marks the active variant)
- Log source: `docker logs email` (Puma access lines include the request duration in seconds)

## Baseline (before the fault)
Window: 2026-11-21 15:54:56Z to 16:01:11Z, 13 readings.

| Metric | Min | Average | Max |
|---|---|---|---|
| Memory | 61.21 MiB | 61.61 MiB | 62.30 MiB |
| Memory % of 100 MiB limit | 61.2% | 61.6% | 62.3% |
| CPU % | 0.03% | 1.51% | 5.22% |
| PIDs | 22 | | 23 |
| `POST /send_order_confirmation` duration | about 0.003 s | | about 0.02 s |

Memory is flat (trend about +0.03 MiB/min). CPU spikes of 4 to 5% appear when orders complete, so they are normal.

## Fault timeline (UTC)

| Variant | First reading | Last reading | Readings | Switch time (known range) |
|---|---|---|---|---|
| `100x` | 16:02:27 | 16:11:26 | 18 | flag turned on between 16:01:11 and 16:02:27 |
| `1000x` | 16:12:26 | 16:16:35 | 9 | switched between 16:11:26 and 16:12:26 |
| `10000x` | 16:17:29 | 16:20:04 | 6 | switched between 16:16:35 and 16:17:29 |

The exact click times were not recorded. Capture was stopped and restarted at each switch, so there are gaps of about 1 minute at each switch.

The 16:02:27 reading was logged to the baseline file by mistake. It is moved to the fault file here. It still shows 61.44 MiB, so no effect was visible yet.

## Results by variant (memory)

| Variant | Memory range | Average | Peak | Trend (MiB/min, rough) |
|---|---|---|---|---|
| Baseline | 61.2 to 62.3 MiB | 61.6 MiB | 62.3 MiB | +0.03 |
| `100x` | 61.4 to 73.8 MiB | 68.6 MiB | 73.83 MiB (73.8%) | +1.2 |
| `1000x` | 75.1 to 92.8 MiB | 86.0 MiB | 92.83 MiB (92.8%) | +3.0 |
| `10000x` | 79.5 to 89.7 MiB | 84.2 MiB | 89.65 MiB (89.7%) | +3.0, driven by one jump at 16:19:33 |

Highest reading: 92.83 MiB at 16:14:00Z.

## Results by variant (request duration, from `docker logs email`)

| Variant | `POST /send_order_confirmation` duration | vs baseline |
|---|---|---|
| Baseline | about 0.003 to 0.02 s | |
| `100x` | about 0.004 to 0.027 s | no visible change |
| `1000x` | mostly 0.02 to 0.04 s, one at 0.1635 s (16:12:48) | about 2 to 3x slower |
| `10000x` | 0.2106 to 0.4435 s (6 of 9 requests above 0.2 s) | about 20 to 40x slower |
| After revert and restart | 0.0166 s, 0.0025 s, 0.0127 s, 0.0027 s, ... | back to baseline |

The request duration is a clearer symptom than memory for the highest variant. Response time grows with the variant because the email body padding is larger.

## Container restarts found in the logs
`docker logs email` shows the service starting several times (the "Sinatra has taken the stage" and Puma startup lines). The container uptime began at 11:39:33Z.

| Startup (UTC) | Preceded by a graceful stop line? | Interpretation |
|---|---|---|
| 16:19:41 | No (last request at 16:19:08, duration 0.2360 s) | Likely killed abruptly while at `10000x`, probably OOM, then restarted automatically |
| 16:22:18 | No (last request at 16:21:09, duration 0.2877 s) | Likely a second abrupt kill, probably OOM, while the flag was still on |
| 16:22:44 | Yes ("Gracefully stopping" after the 16:22:27 request) | The manual `docker restart email` |

- Treat the two abrupt restarts as probable OOM kills. The logs alone cannot prove the cause.
- The stats readings after 16:19:41 come from a restarted process, so the 16:20:04 reading is not a continuation of the earlier curve.
- `docker inspect` printed `OOMKilled=false Restarts=0`, but this was run after the manual `docker restart`, which resets both values. It does not rule out earlier OOM kills.
- To confirm: `docker events --since 2026-11-21T16:15:00 --until 2026-11-21T16:30:00 --filter container=email` (look for `oom` and `die` events). Docker Desktop keeps events only for a limited time, so it may be empty.

## Revert
- Flag set to `off`: between 16:21:09Z and 16:22:27Z (the 16:22:27 request already took only 0.0738 s, versus 0.21 to 0.44 s earlier). Exact time: <time>
- `docker restart email`: about 16:22:3xZ (graceful stop, startup at 16:22:44Z)
- After restart: `docker stats email` shows 42.5 MiB (42.5%), CPU 0.09%, PIDs 23. This is lower than the baseline average (61.6 MiB) because the process is new.
- Request durations after the restart are 0.0025 to 0.0166 s, which is baseline.

## What the data shows
- **Memory grows in a sawtooth, not a smooth line.** It climbs, then drops (for example 73.83 -> 67.61 MiB at 16:06:45, and 92.83 -> 90.04 -> 88.85 MiB after 16:14:00). Garbage collection reclaims part of it.
- **Higher variants raise the level quickly.** At `1000x` the peak reached 92.83 MiB, and at `10000x` the container was likely killed twice by the memory limit.
- **Request duration is the strongest signal at `10000x`.** It rose 20 to 40 times while CPU stayed in the baseline range.
- **CPU is not the signal.** It stayed in the baseline range (spikes up to 6.15%).
- **Memory peaks are sudden.** The jumps (66.3 -> 73.8 MiB at 16:06:14, 78.6 -> 92.8 MiB at 16:14:00, 79.5 -> 89.2 MiB at 16:19:33) line up with PIDs rising or CPU spikes of 2 to 6%, which fits an order completing and a large email body being built.
- **No error lines appear in the logs.** Every request returned `200`. The fault is visible only in memory, request duration and restarts.

## Evidence
| Signal | Where | What I saw |
|---|---|---|
| Metrics | `docker stats email` | Memory rose from about 61.6 MiB to 89 to 93 MiB, with a sawtooth pattern |
| Logs | `docker logs email` | All requests `200`. Duration rose to 0.21 to 0.44 s at `10000x`. Startup banners at 16:19:41 and 16:22:18 with no graceful stop line before them |
| Metrics | Grafana, `email` memory | <present or empty> |
| Traces | Jaeger, `email` spans | <duration change, expected to match the 0.2 to 0.4 s seen in the logs> |
| Container state | `docker events` | <oom/die events, if still available> |

## Red herrings and gotchas
- Memory is not a straight line, and it can drop. An agent that only checks "is memory growing in every sample" will miss it. Compare the average or peak against baseline instead.
- No error-level or warning logs exist. A log search for errors finds nothing, because the only hints are slow requests and restarts.
- A restart in the logs looks like a crash, but it can also be the user's own `docker restart` (the graceful-stop line tells them apart).
- `docker inspect` right after a manual restart shows `OOMKilled=false Restarts=0`, even if earlier OOM kills happened.
- CPU spikes of 4 to 6% are normal order activity, not evidence of the fault.
- `email` only changes when orders complete, so low traffic hides the symptom.
- The first `docker stats` baseline of `email` was 58.3 MiB, and this scenario's baseline is 61.6 MiB, so use this scenario's own numbers.
- Slow requests of 0.09 to 0.21 s appear in the logs at 13:30 to 13:32 UTC, which is before this scenario. They are probably from earlier testing, so they are not part of this ground truth.

## Root cause
`email` service, injected through the `emailMemoryLeak` flag. The variant controls how much each confirmation email body is padded. Symptoms: memory rising toward the 100 MiB limit, slower `send_order_confirmation` requests at high variants, and probable OOM restarts, with no error logs.
