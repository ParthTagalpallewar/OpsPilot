# OpsPilot AI

**An AI-powered SRE and DevOps incident investigation agent.**

OpsPilot investigates production incidents the way an on-call engineer would: it reads logs, checks metrics and traces, correlates findings with recent deployments, searches runbooks, and reports ranked root-cause hypotheses, each backed by cited evidence. A human approves every remediation before anything runs.

> **Status:** runnable local replay demo. The API, worker, and CLI share an evidence-first LangGraph workflow for three frozen scenarios. The local deployment uses SQLite. See [Getting started](#getting-started) for the Docker demo and [Roadmap](#roadmap) for the target architecture.

---

## Table of contents

- [Why OpsPilot](#why-opspilot)
- [Example](#example)
- [How it works](#how-it-works)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [Evaluation](#evaluation)
- [Safety and security](#safety-and-security)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Learn or continue the project

Read the [beginner walkthrough](Concepts/00-project-walkthrough.md) to follow
an incident from evidence to review. The [developer handoff](docs/developer-handoff.md)
covers current verification and the Kubernetes starting point.

## Why OpsPilot

When a payment API starts returning 500 errors after a release, an engineer typically has to check application logs, review CPU and memory, look at recent deployments, search internal docs, and then decide on a fix. OpsPilot automates that investigation loop.

The core design rule: **the agent investigates real data and never invents a root cause.**

- **Deterministic code does the numbers.** Time-window correlation with deployments, error counts, and metric thresholds are plain, testable Python.
- **The LLM reasons over evidence.** It proposes hypotheses and explains them, but every claim must cite an evidence ID.
- **Humans stay in control.** Remediation is dry-run only in v1, and always requires approval.

## Example

**Prompt:** "Why is our payment service returning 500 errors after the latest deployment?"

**Report:**

| Field | Output |
|---|---|
| Problem | Payment API returning 500 errors |
| Observation | Database connection timeouts increased after the deployment |
| Evidence | `ev_8f3a` (log cluster: `ConnectionTimeout` x412, baseline 3), `ev_21c9` (deploy event with config diff) |
| Possible root cause | Connection pool configuration changed |
| Recommended action | Verify connection pool settings and compare with the previous deployment |
| Confidence | Rule-capped, based on available evidence. Not an independently verified diagnosis |

## How it works

In the runnable demo, FastAPI or the CLI selects a scenario and LangGraph
builds a cited report. The API can queue a replay in SQLite or PostgreSQL.
A separate worker processes the job, and clients can follow its progress over
SSE. Reviewers can edit, reject, or approve a dry-run plan and retrieve the
saved decision and preview.

Follow the [portfolio demo](docs/portfolio-demo.md) for a reproducible
walkthrough and resume bullets.

### Target architecture

```
 Engineer/UI ──REST/SSE──┐        Alertmanager ──webhook──┐
                         ▼                                 ▼
                 ┌───────────────────────────────────────────┐
                 │          API  (FastAPI, stateless)         │
                 └───────┬───────────────────────┬───────────┘
                enqueue  │                       │ read/write
                         ▼                       ▼
                  ┌────────────┐      ┌────────────────────────────┐
                  │   Redis    │      │ PostgreSQL + pgvector      │
                  │ queue·cache│      │ incidents · evidence · logs│
                  │ pub/sub    │      │ deploys · chunks · plans   │
                  └─────┬──────┘      │ approvals · audit · ckpts  │
                        │ job         └─────────────▲──────────────┘
                        ▼                           │
                ┌──────────────────┐                │
                │  Agent worker    │──▶ Evidence tools (packages/evidence)
                │  (LangGraph)     │     logs│metrics│traces│deploys│rag
                └───┬─────────┬────┘
                    ▼         ▼
               Claude API   Langfuse
```

**Investigation flow**

1. `POST /v1/incidents` stores the incident, enqueues a job, and returns `202` with an investigation ID.
2. A worker runs the LangGraph workflow and streams progress to the UI over SSE.
3. Evidence tools run in parallel. Each result is stored as an immutable `evidence` row.
4. Plain code correlates the evidence; the LLM then proposes hypotheses citing evidence IDs.
5. A validator checks the schema and citations, then the graph pauses for human approval.
6. `POST /v1/investigations/{id}/approval` resumes the graph. The decision and the dry-run plan are written to an append-only audit log.

**Agent graph**

```
START → triage → plan → ┬ logs ────┐
                        ├ metrics ─┤
                        ├ traces ──┼→ correlate (code) → hypothesize (LLM)
                        ├ deploys ─┤                          │
                        └ runbooks ┘        need more evidence? ──yes→ plan (max 2 loops)
                                                              │ no
                                  validate (citations+schema) → report → interrupt(approval) → [later] execute
```

For the full design, including the data model, caching, error handling, scaling, and trade-offs, see the workspace system design notes in `../systemDesign.txt`.

## Features

| Feature | Priority | Status |
|---|---|---|
| RAG over technical documentation (hybrid vector + keyword search) | Must have | Planned |
| Log ingestion and analysis | Must have | Planned |
| Agent tool calling | Must have | Planned |
| LangGraph workflow | Must have | Planned |
| Correlation with deployment events | Must have | Planned |
| Evidence-based root cause analysis | Must have | Planned |
| Evaluation framework | Must have | Planned |
| Human approval before remediation | Must have | Planned |
| Observability and tracing | Must have | Planned |
| Automated remediation | Later | Out of scope for v1 |

## Tech stack

| Area | Technology |
|---|---|
| Language | Python (managed with [uv](https://docs.astral.sh/uv/)) |
| API | FastAPI |
| Agent orchestration | LangGraph (Postgres checkpointer) |
| LLM | Claude API |
| Embeddings | Sentence Transformers |
| Database | PostgreSQL |
| Vector search | pgvector (HNSW) with `tsvector` for hybrid search |
| Queue, cache, pub/sub | Redis |
| Containers | Docker |
| Deployment | Kubernetes (local cluster) |
| CI/CD | GitHub Actions |
| LLM observability | Langfuse |
| Testing | pytest |

The stack is introduced incrementally. Components are added when the project needs them.

## Project structure

```
.
├── opspilot/
│   ├── apps/
│   │   ├── api/            # FastAPI backend
│   │   └── worker/         # Queue worker that runs replays
│   ├── evidence/           # Deterministic, read-only evidence collectors
│   ├── replay.py           # LangGraph replay workflow
│   ├── investigations.py   # Investigation, job, and approval storage
│   ├── evaluation.py       # Scoring against ground truth
│   └── cli.py              # `opspilot` command
├── testbed/
│   ├── scenarios/          # Frozen telemetry for the three demo scenarios
│   ├── captures/           # Additional measured and edge-case captures
│   ├── ground_truth/       # Expected report contents used for scoring
│   └── runbooks/           # Markdown runbooks used for retrieval
├── infra/
│   ├── docker/             # Compose files, smoke test, and benchmark
│   └── kubernetes/         # Local cluster manifests
├── tests/                  # pytest suite
├── .github/workflows/      # GitHub Actions CI pipeline
├── .python-version
├── pyproject.toml
└── uv.lock
```

| Directory | Responsibility |
|---|---|
| `opspilot/apps/api` | FastAPI backend: incident intake, SSE streaming, approvals, evidence lookup |
| `opspilot/apps/worker` | Worker that claims queued jobs and runs the replay workflow |
| `opspilot/evidence` | Deterministic, read-only tools for logs, metrics, traces, deployments, and runbook retrieval. Plain Python, with no LLM calls |
| `testbed/scenarios` | Frozen telemetry so investigations can be replayed deterministically |
| `testbed/captures` | Measured captures and edge cases (healthy, ambiguous, cross-service) |
| `testbed/ground_truth` | Expected evidence and causes for every evaluated case |
| `infra/docker` | Docker Compose for the demo, PostgreSQL, and Redis |
| `tests` | Unit and API tests |
| `.github/workflows` | CI pipeline |

## Getting started

### Replay a captured incident

Run from the repository root after installing dependencies:

```bash
uv run opspilot replay ad-high-cpu
uv run opspilot replay email-memory-leak
uv run opspilot replay payment-failure
```

A LangGraph workflow routes each replay to its evidence collectors and validates
report citations. The CLI returns a JSON report with cited evidence from captured Docker stats or
Payment logs. Resource captures include baseline comparisons and documented flag
change intervals. The Payment capture
contains a single warning excerpt preserved from the scenario notes. Each replay
can also cite a runbook section from `testbed/runbooks` as troubleshooting guidance.

Add `--format markdown` to print the same report as a Markdown summary for an
incident channel or ticket. Every statement keeps its evidence IDs, and text
quoted from telemetry is escaped so it cannot add links, HTML, or headings.

Read the [concept lessons](Concepts/README.md) and the
[development log](progress/2026-11-22-shared-compose.md).

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (it installs the Python version pinned in `.python-version` for you)
- [Docker](https://docs.docker.com/get-docker/) (needed once the local services are added)
- An Anthropic API key (needed once the agent is wired up)

### Quick start

```bash
git clone https://github.com/<your-username>/opspilot.git
cd opspilot

# Install dependencies
uv sync

# Verify the setup
uv run pytest
```

To retrieve a known failed Payment trace from a local Jaeger v3 API, run
`uv run opspilot capture-payment-trace --url http://localhost:16686 --trace-id ID --output PATH`.
Then run `uv run opspilot replay payment-failure --captures PATH`. You can also
place a saved OTLP JSON export named `payment-traces.json` in that directory.
The report cites Payment error spans and identifies their parent spans when the
export includes them. A Payment log can be linked to its exact failed span
by including both `trace_id` and `span_id` in the log record.

For a historical report, add a UTC-offset cutoff such as
`--as-of 2026-11-21T14:31:25Z`. The API accepts the same value as `as_of`.
The replay computes its findings from evidence visible by that timestamp.

### Enable hybrid runbook retrieval

```bash
uv sync --extra semantic
OPSPILOT_RUNBOOK_SEARCH=hybrid uv run --extra semantic opspilot replay payment-failure
```

The model is downloaded on first use. Vectors are computed locally and combined
with keyword rankings. Use the same environment setting and installed extra on
the worker to enable hybrid retrieval for queued investigations.

To persist embeddings across runs, start the local pgvector database and set
`OPSPILOT_VECTOR_DSN` to its PostgreSQL connection string while hybrid retrieval
is enabled:

```bash
docker compose -f infra/docker/docker-compose.yml up -d postgres
```

New database volumes apply the vector schema at initialization. On an existing
volume, apply the idempotent migration:

```bash
docker compose -f infra/docker/docker-compose.yml exec -T postgres \
  sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < infra/docker/postgres/init/02-runbook-vectors.sql
```

### Capture a Prometheus comparison

Run `uv run opspilot capture-metrics --help` for arguments. Choose Ad or Email,
a Prometheus base URL, a PromQL expression returning one percentage series, and
four timestamps with UTC offsets for the baseline and incident windows. Write
the result to a separate capture directory, then run
`uv run opspilot replay ad-high-cpu --captures PATH` for an Ad capture. Use
`email-memory-leak` for an Email capture.

To add an OTLP JSON log export to that capture directory, run
`uv run opspilot import-payment-logs EXPORT.json --output PATH`. The importer
selects timestamped Payment warnings and errors with text bodies and preserves
their trace and span IDs when present.

For a measured example, replay the
[controlled Payment capture](testbed/captures/payment-controlled/README.md).
It contains matched warnings, failed spans, and request counts. The
[Checkout-to-Payment capture](testbed/captures/checkout-payment/README.md)
also shows how the failure propagated to Checkout.

### Import Kubernetes rollout evidence

Export ReplicaSets from your local cluster and freeze the records for one
Deployment into the directory holding its metric capture:

```bash
kubectl get replicasets -n demo -o json > replicasets.json
uv run opspilot import-rollouts ad-high-cpu replicasets.json \
  --namespace demo --deployment ad --output PATH
uv run opspilot replay ad-high-cpu --captures PATH
```

Replay can correlate ReplicaSet creation with metric changes. To verify rollout
completion or user impact, compare readiness and request telemetry.

### Request a Claude explanation

Set `ANTHROPIC_API_KEY` and `OPSPILOT_CLAUDE_MODEL` in your shell, then run
`uv run opspilot replay ad-high-cpu --with-claude`. This sends the demo's
aggregate evidence and any reviewed runbook section to the Claude Messages API.
Run the standard replay command for an offline report.

### Run the local replay API

From the repository root, start the API with:

```bash
uv run uvicorn opspilot.apps.api.main:local_app --factory
```

Open `http://127.0.0.1:8000/docs` and submit a `POST /v1/incidents` with a
`title` and `description`. For example, “Payment API returning 500” routes to
the Payment replay. You can supply a `service` hint or choose an explicit
`scenario` such as `ad-high-cpu`.
Retrieve the saved report at `GET /v1/investigations/{investigation_id}`.
If the report includes a plan, submit `plan_id`, `plan_hash`, and a decision to
`POST /v1/investigations/{investigation_id}/approval`. Use `approve`, `reject`, or
`edit`. For an edit, send replacement action text in `edits` and review the new
plan returned by the API. Approval records a dry-run preview of the exact
reviewed action and its evidence.

The server uses `opspilot.sqlite3` by default. Set `OPSPILOT_DB` to change
the database file or `OPSPILOT_CAPTURES` to change the capture directory.

For asynchronous replay, include `"queued": true` in the incident request.
The API returns HTTP 202 with a `Location` for checking progress. Start a worker
from the same directory with the same database and capture settings:

```bash
uv run python -m opspilot.apps.worker.main
```

Use `--once` to process at most one job. Watch status transitions and completed
LangGraph steps at
`GET /v1/investigations/{investigation_id}/events`. Supply `Last-Event-ID` to
resume from a previous event. Retrieve a cited record at
`GET /v1/investigations/{investigation_id}/evidence/{evidence_id}`.

### Run the packaged demo

```bash
docker compose -f infra/docker/replay.compose.yml up --build --wait
python3 infra/docker/smoke_replay.py
docker compose -f infra/docker/replay.compose.yml down
```

The API and worker share a named volume for the local investigation database.
The API is available on loopback port 8000. Set `OPSPILOT_PORT` to use another port.

### Run the PostgreSQL and Redis demo

```bash
export COMPOSE_FILE=infra/docker/replay.compose.yml:infra/docker/shared.compose.yml
docker compose up --build --wait
python3 infra/docker/smoke_replay.py
docker compose down
```

The overlay runs PostgreSQL and Redis on the Compose network, publishes the
API on loopback, and persists the investigation and graph checkpoint tables
in a named PostgreSQL volume. It uses development credentials for local use.

### Run on a local Kubernetes cluster

Use a local cluster with a default StorageClass. Build the demo image and
make it available to the cluster's node runtime. For a kind cluster:

```bash
docker build -t opspilot-replay:local .
kind load docker-image opspilot-replay:local
kubectl apply -k infra/kubernetes
kubectl rollout status deployment/opspilot-replay
kubectl port-forward service/opspilot-replay 8000:8000
```

In another terminal, run `python3 infra/docker/smoke_replay.py`. The API and
worker run in one Pod and share the replay database on a persistent claim.

### Queue a replay from Alertmanager

Configure a webhook receiver for `POST /v1/webhooks/alertmanager`. Tag a demo
alert rule with `opspilot_scenario` set to `ad-high-cpu`, `email-memory-leak`, or
`payment-failure`. The webhook accepts firing alerts with one of those values,
and the local worker processes the corresponding frozen captures. Repeat
deliveries with the same fingerprint and start time reuse the investigation.

### Capture fresh metrics from an alert

Set `OPSPILOT_PROMETHEUS_URL` and at least one of `OPSPILOT_PROMQL_AD` or
`OPSPILOT_PROMQL_EMAIL` in both the API and worker. Set `opspilot_mode: live`
and the corresponding `opspilot_scenario` on the alert. Each configured
expression must return one percentage series. The worker queries the baseline
and incident windows ending near the alert time, then writes a snapshot under
`OPSPILOT_LIVE_CAPTURES` (default `live-captures/`).

Configure a shared writable capture directory if multiple workers may reclaim
a job. The report can be reproduced with the CLI using the investigation's
capture directory.

For Payment, set `OPSPILOT_JAEGER_URL` in both processes. Use
`opspilot_mode: live` and `opspilot_scenario: payment-failure` as the alert
labels. The worker searches up to 20 Payment traces in the ten minutes before
the alert for a completed failed span. To pin a known trace, supply a
32-character hexadecimal ID in the optional `opspilot_trace_id` annotation.
Include Jaeger's configured URL prefix in `OPSPILOT_JAEGER_URL` (for example,
`http://localhost:8080/jaeger/ui` in the OpenTelemetry Demo). The worker saves
the selected failed trace
under the same capture root. Optionally set `OPSPILOT_PAYMENT_LOG_EXPORT`
on the worker to a readable OTLP JSON or Collector file-exporter JSONL file.
The worker freezes warnings for the chosen trace and marks coverage partial
if the configured export has no match or cannot be read. To add aggregate
rates, set `OPSPILOT_PROMETHEUS_URL` and `OPSPILOT_PROMQL_PAYMENT_FAILURE_RATE`
on the worker. The query must return one percentage series in the range
0 to 100. The report displays the mean sampled rate for each window.

For the OpenTelemetry Demo, the following query uses the Collector's
span-derived counter. Server spans count the Payment side of the request.
The fallback supplies a zero numerator when no error series exists, and the
denominator filter leaves samples absent when there is no request traffic.

```promql
100 * (
  sum(rate(traces_span_metrics_calls_total{service_name="payment",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"}[5m]))
  or 0 * sum(rate(traces_span_metrics_calls_total{service_name="payment",span_kind="SPAN_KIND_SERVER"}[5m]))
) / (sum(rate(traces_span_metrics_calls_total{service_name="payment",span_kind="SPAN_KIND_SERVER"}[5m])) > 0)
```

### Configure authenticated API access

Set `OPSPILOT_API_CREDENTIALS` to a JSON file containing a list of objects
with `principal`, `role`, and `token`. Generate distinct tokens with
`python3 -c 'import secrets; print(secrets.token_urlsafe(32))'` and keep the
file outside the repository. Send tokens as `Authorization: Bearer TOKEN`.

Operators submit incidents and read reports. Reviewers read reports and
record plan decisions. Webhook credentials can only submit Alertmanager
notifications. Use HTTPS for shared deployments. With no credentials file,
the API is in local demo mode.

### Use a shared PostgreSQL investigation store

Start PostgreSQL and install the optional client:

```bash
docker compose -f infra/docker/docker-compose.yml up -d postgres
uv sync --extra postgres
```

Set `OPSPILOT_DATABASE_DSN` to the database connection string in the shell
for both processes. The app initializes its tables when it starts. Run the
same API and worker commands above with `uv run --extra postgres`. If you also
enable semantic retrieval, include `--extra semantic`. A PostgreSQL database
starts with its own investigation history. Existing SQLite records remain
in the original database file. PostgreSQL-backed workers also save LangGraph
checkpoints and resume reclaimed replays at the next pending node.
Each PostgreSQL-backed dry-run plan also waits on a durable approval interrupt.
The approval decision resumes that thread and commits with the audit event.

### Enable Redis worker notifications

```bash
docker compose -f infra/docker/docker-compose.yml up -d redis
uv sync --extra redis
```

Set `OPSPILOT_REDIS_URL` in the API and worker shells and include
`--extra redis` in their `uv run` commands. Keep any other enabled extras.
The optional `OPSPILOT_REDIS_KEY` separates wake-up channels for deployments
sharing a Redis database. Jobs and status events stay in the investigation database.

### Running the testbed (planned)

OpsPilot is evaluated against the [OpenTelemetry Demo](https://opentelemetry.io/docs/demo/) with deliberately injected faults. Scenario scripts in `testbed/scenarios` will inject each fault and capture the resulting telemetry into `testbed/snapshots`.

## Configuration

OpsPilot reads configuration only from environment variables; it does not load a `.env` file. The most common settings:

| Variable | Purpose |
|---|---|
| `OPSPILOT_DB` | SQLite database file (default `opspilot.sqlite3`) |
| `OPSPILOT_DATABASE_DSN` | PostgreSQL connection string; takes precedence over `OPSPILOT_DB` |
| `OPSPILOT_CAPTURES` | Replay capture directory (default `testbed/scenarios`) |
| `OPSPILOT_REDIS_URL`, `OPSPILOT_REDIS_KEY` | Optional Redis worker wake-up |
| `OPSPILOT_API_CREDENTIALS` | Bearer credentials file; unset means local demo mode |
| `ANTHROPIC_API_KEY`, `OPSPILOT_CLAUDE_MODEL` | Optional Claude explanation (`--with-claude`) |
| `OPSPILOT_PROMETHEUS_URL`, `OPSPILOT_PROMQL_AD`, `OPSPILOT_PROMQL_EMAIL`, `OPSPILOT_PROMQL_PAYMENT_FAILURE_RATE`, `OPSPILOT_JAEGER_URL`, `OPSPILOT_PAYMENT_LOG_EXPORT`, `OPSPILOT_LIVE_CAPTURES` | Live capture for Alertmanager alerts |
| `OPSPILOT_RUNBOOK_SEARCH`, `OPSPILOT_VECTOR_DSN` | Hybrid runbook retrieval |
| `OPSPILOT_TRACING`, `OPSPILOT_METRICS`, `OTEL_EXPORTER_OTLP_*`, `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | Tracing and metrics export |

Never commit `.env`. It is listed in `.gitignore`.

## API overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/incidents` | Submit an incident (`title`, `description`, optional `service`, `reported_at`, `as_of`). Returns `202` with `incident_id` and `investigation_id` |
| `GET` | `/v1/investigations/{id}` | Status, report, and evidence references |
| `GET` | `/v1/investigations/{id}/events` | Server-sent events stream of investigation progress |
| `POST` | `/v1/investigations/{id}/approval` | Approve, edit, or reject a remediation plan |
| `GET` | `/v1/investigations/{id}/evidence/{evidence_id}` | Raw evidence, so any claim in a report can be audited |
| `GET` | `/v1/investigations/{id}/summary` | Markdown summary of a completed report (`409` until the report exists) |
| `POST` | `/v1/webhooks/alertmanager` | Map an Alertmanager alert to an incident |

## Observe an investigation

Set `OPSPILOT_TRACING=console` to print OpenTelemetry spans to stderr. To export
over OTLP HTTP, set `OPSPILOT_TRACING=otlp` and
`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` to your collector's traces endpoint.
Enable tracing on both the API and worker to see queue context propagation.

To send evaluator observations to a Langfuse project, set
`OPSPILOT_TRACING=langfuse`, `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, and
`LANGFUSE_SECRET_KEY`, then run `uv run opspilot eval`. The terminal still
receives the evaluation JSON. The exported observations contain aggregate
checks and a reference dataset hash.

Set `OPSPILOT_METRICS=console` to inspect operational metrics on stderr, or
use `OPSPILOT_METRICS=otlp` with `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`. The API
observes available queue depth and approval wait. Workers report finalized
outcomes and processing duration. The optional Claude client records token usage
when available.

To measure the queued replay path against either running Compose demo, run
`python3 infra/docker/benchmark_replay.py --jobs 30 --concurrency 5`. The
benchmark reports HTTP enqueue-to-completion latency from the SSE stream,
excluding human review. It uses the local frozen captures.

## Evaluation

Run `uv run opspilot eval` from the repository root to check the frozen demo
reports against the reference expectations. The command prints JSON with
per-scenario results and returns exit status 1 when any scenario fails. Ad and
Email also check that a unique leading hypothesis matches the recorded injected
cause. Payment checks that the report withholds a hypothesis.

Run `uv run opspilot eval --ground-truth testbed/ground_truth/extended.json`
to check healthy readings, conflicting changes, look-ahead prevention, and
the measured Checkout-to-Payment log and span links. CI runs both suites.


OpsPilot has no real production incidents to learn from, so it makes its own:

- **Fault injection:** known faults (bad config, slow database, memory leak) are injected into the OpenTelemetry Demo, and the real logs, metrics, and traces are collected. Public datasets such as [Loghub](https://github.com/logpai/loghub) can supplement them.
- **Ground truth:** every scenario has a recorded root cause in `testbed/ground_truth`, so the agent can be scored on how often it finds it.
- **Deterministic replay:** each scenario's telemetry is frozen as a snapshot, and every evidence tool accepts an `as_of` clock override. Results are comparable across prompt and model changes.
- **Tracking:** scores are logged to Langfuse as experiment runs.

## Safety and security

- **Read-only tools.** Telemetry access uses read-only credentials.
- **Logs are untrusted input.** Log content is wrapped as quoted data and can never change tool permissions or agent behavior.
- **Model context.** Claude receives selected demo summaries and reviewed runbook text. Raw logs and free-text incident content stay local.
- **Human approval.** Nothing is executed without explicit approval, and plans expire after a TTL. Approvals are bound to a hash of the exact plan that was reviewed.
- **Budget guards.** Hard caps on steps and tokens per investigation. When a cap trips, the agent returns a partial report.
- **Rule-capped confidence.** Confidence is computed from temporal alignment, agreeing evidence types, runbook match, and contradicting evidence. The LLM can explain it but cannot raise it.

## Roadmap

- [x] Repository skeleton and system design
- [ ] Evidence data model and Pydantic contracts
- [ ] Postgres schema and migrations
- [ ] Evidence tools: logs, metrics, traces, deployments
- [ ] Runbook RAG with hybrid search
- [ ] Testbed: fault injection and telemetry snapshots
- [x] LangGraph replay workflow with PostgreSQL checkpoint recovery
- [ ] FastAPI service, job queue, and SSE streaming
- [x] Human approval, audit history, and PostgreSQL-backed interrupts
- [ ] Evaluation harness and baseline scores
- [ ] Langfuse tracing and OpenTelemetry instrumentation
- [ ] Docker images, Kubernetes manifests, and CI
- [ ] Automated remediation (later, behind a policy engine)

## Contributing

This is currently a solo project, but feedback is welcome. To propose a change, open an issue to discuss it first. Before submitting a pull request:

1. Create a feature branch from `main`.
2. Add or update tests in `tests/`.
3. Run `uv run pytest` and make sure it passes.
4. Open a pull request describing the change.

## License

Choose a license and add a `LICENSE` file, for example [MIT](https://choosealicense.com/licenses/mit/). Then replace this section with the license name.