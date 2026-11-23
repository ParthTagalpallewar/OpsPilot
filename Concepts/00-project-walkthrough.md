# Understand OpsPilot from the ground up

OpsPilot investigates reports that a software service is behaving badly.
It gathers records, compares what happened before and during the problem,
and produces a report you can check against those records. Each important
claim points to the evidence behind it. A human can review a proposed
follow-up and approve a dry-run preview.

## 1. Start with one incident

Imagine the Ad service suddenly uses a lot of CPU. An engineer wants to
know when it changed, what else changed around that time, and what to
check next. Usually those answers live in different places. OpsPilot
collects the relevant pieces into one investigation.

From the repository root, install dependencies with `uv sync`, then run:

```sh
uv run opspilot replay ad-high-cpu > /tmp/opspilot-ad-report.json
python3 -m json.tool /tmp/opspilot-ad-report.json
```

A **replay** investigates saved evidence. It lets you study the same
incident repeatedly without waiting for a real outage. This example needs
Python and the project dependencies. The API, Docker, and model credentials
are optional for this exercise.

Open the JSON and follow this sequence.

| Report section | What to look for |
|---|---|
| `observations` | The saved samples show 0.74% mean CPU in the baseline and 398.00% during the fault. In this Docker CPU measure, about 100% corresponds to one fully busy logical CPU, so 398% is roughly four CPUs' worth of activity. |
| `evidence` | Look up `ev_ad_baseline_all`, `ev_ad_fault_all`, and `ev_change_ad_2`. The first two summarize measurements. The third records when the `adHighCpu` flag may have changed. |
| `hypotheses` | The flag change fits the gap between the last baseline sample and first fault sample. The report calls it a possible contributor with low confidence because timing alone leaves other explanations open. |
| `guidance` | A retrieved runbook gives a practical check. A runbook is a troubleshooting guide, and its presence tells you what to investigate next. |

Now run `uv run opspilot replay payment-failure`. The default Payment capture
contains a warning, and the report leaves its hypothesis empty. Then run
`uv run opspilot replay payment-failure --captures testbed/captures/checkout-payment`.
Find the observation that cites both a warning and a failed span. They share a
trace ID and a span ID, so OpsPilot can point to the exact operation that logged
the warning. The report still leaves causal attribution open.

**Check your understanding.** The CPU increase is an observation. The flag
contributing to it is a hypothesis. Verifying the change timeline and checking
request traffic are follow-ups. Being able to tell these apart is the first
step toward reading any OpsPilot report.

## 2. Learn the kinds of evidence

| Term | Meaning in OpsPilot |
|---|---|
| Incident | A report of a possible problem. The API receives a title, description, and optional service or scenario. |
| Investigation | The job and saved result created from an incident. Its ID lets you fetch the report, events, and cited evidence. |
| Metric | A number measured over time. CPU can rise and fall. A request counter accumulates calls and may reset on restart. Prometheus can estimate the rate of increase between scrapes. |
| Log | A message emitted by an application. It may include a timestamp, severity, and IDs that connect it to a request. |
| Trace and span | A trace follows one request across services. A span describes one operation in that trace. A parent span can show that Checkout called Payment. |
| Change event | A timestamp or interval for a change, such as enabling a flag or starting a rollout. Its timing helps rank possible causes. |
| Baseline and fault windows | Two time ranges used for comparison. A baseline approximates normal behavior and a fault window covers the suspected problem. |
| Citation | An evidence ID attached to a claim. It lets a reader inspect the record the claim depends on. |
| Historical cutoff | An `as_of` timestamp that limits the report to records visible by that point. This lets you ask what the investigator could have known at the time. |

## 3. Follow the work from request to report

```text
CLI replay ────────────────────────────────────────┐
                                                  v
API incident or Alertmanager -> saved job -> worker -> evidence -> report
                                 |                    |             |
                                 v                    v             v
                             database           capture files   review plan
                                 |
                                 v
                           progress events
```

1. **Intake.** FastAPI validates an incident or webhook. An incident can select
   a scenario explicitly or use the supported service and text hints.
   Alertmanager supplies a fingerprint and a start time. OpsPilot uses the pair
   to recognize repeat deliveries of the same alert occurrence.
2. **Queue.** A queued request returns HTTP 202, which means the job was
   accepted. The database stores the job. The worker claims it using a lease,
   a time-limited claim that enables another worker to reclaim abandoned work.
   Redis can wake a waiting worker promptly in shared mode. The database
   remains the authoritative job store.
3. **Capture.** A replay reads saved files. A live alert can have the worker
   fetch telemetry and save an investigation-specific snapshot first. The
   snapshot lets you inspect or replay the evidence later. Payment can search
   Jaeger near the alert time, use an optional OTLP log export, and compare
   live Prometheus failure rates.
4. **Investigate.** LangGraph runs a workflow made of named steps. State is
   the data passed between steps. The graph chooses either the resource or
   Payment path, collects evidence, builds a report, retrieves runbook
   guidance, and checks that claim citations resolve. Python handles
   numeric summaries and timestamp comparisons. Optional Claude explanation
   runs on validated report evidence when requested.
5. **Save and stream.** The worker saves the result and records progress
   events. Server-sent events (SSE) let a client watch these updates over one
   HTTP connection. A reconnect can send the last event ID to continue
   reading. PostgreSQL mode also supports LangGraph checkpoints that record
   workflow state for recovery.
6. **Review.** When a report proposes a follow-up plan, a reviewer can edit,
   reject, or approve it. A plan hash identifies the exact reviewed contents.
   Editing changes that hash, so an approval for the older plan becomes stale.
   The approval creates a dry-run preview and an audit record.

## 4. Read the code in the order it runs

| Start here | What to find |
|---|---|
| [CLI entry point](../opspilot/cli.py) | Commands for replay, metric capture, trace capture, and evaluation. |
| [API](../opspilot/apps/api/main.py) and [webhook](../opspilot/apps/api/alertmanager.py) | How request bodies become investigation records and how duplicate alerts are handled. |
| [Worker entry point](../opspilot/apps/worker/main.py) and [job store](../opspilot/investigations.py) | How a job goes from queued to running to completed or failed. Start with `process_next`. |
| [Investigation graph](../opspilot/replay.py) | Start with `build_replay_graph`. Follow the arrows to the collection and report functions. |
| [Evidence collectors](../opspilot/evidence/) | How files and API responses become named records with timestamps and IDs. |
| [Runbook retrieval](../opspilot/evidence/runbooks.py) | How keyword and optional semantic search find relevant instructions. Keyword search scores matching words. Semantic search compares numeric representations of meaning. |
| [Approval logic](../opspilot/approvals.py) and [approval graph](../opspilot/approval_graph.py) | How the current plan is identified and how the PostgreSQL-backed review workflow waits for a decision. |
| [Evaluator](../opspilot/evaluation.py) | How known scenarios check citations, likely causes, and whether the system abstains when evidence is insufficient. |

## 5. Watch the API and worker separately

Start the API in one terminal and keep it running.

```sh
uv run uvicorn opspilot.apps.api.main:local_app --factory
```

From another terminal in the same repository, submit a queued replay.

```sh
curl -i http://127.0.0.1:8000/v1/incidents \
  -H 'Content-Type: application/json' \
  -d '{"title":"Ad CPU spike","description":"Inspect the saved Ad CPU incident","scenario":"ad-high-cpu","queued":true}'
```

Copy the investigation ID from the response. Fetch the investigation while
it is queued. Start the worker using the same database settings and fetch
the investigation again. The report should appear when the worker completes.

```sh
uv run python -m opspilot.apps.worker.main --once
curl -sS http://127.0.0.1:8000/v1/investigations/INVESTIGATION_ID
```

Append `/events` to the investigation URL to see its progress history.
Append `/evidence/ev_ad_baseline_all` to look up the baseline record.
See the [portfolio walkthrough](../docs/portfolio-demo.md) for a guided
approval demo.

## 6. Connect this to deployment

Docker packages the Python runtime, dependencies, and OpsPilot code into an
image. Kubernetes runs that image in Pods and replaces Pods when needed. A
Service gives the API a stable address. A persistent volume or an external
database keeps durable state available when Pods are replaced.

The API accepts requests, and the worker spends time doing investigations.
Running them as separate workloads eventually lets you scale them separately.
Both still need to agree on where the durable jobs, checkpoints, and capture
files live. The current Kubernetes demo uses one Pod with two containers and
a SQLite volume. The [Kubernetes lesson](17-kubernetes-local-deployment.md)
explains that layout, and the [developer handoff](../docs/developer-handoff.md)
describes the deployment milestones.

**You are ready to start deployment work when you can explain** where a queued
job lives, which process claims it, where evidence files are saved, and what
happens to each piece if the Pod restarts. Use the [Concepts index](README.md)
to revisit any step in more detail.
