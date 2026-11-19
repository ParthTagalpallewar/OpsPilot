# OpsPilot AI

**An AI-powered SRE and DevOps incident investigation agent.**

OpsPilot investigates production incidents the way an on-call engineer would: it reads logs, checks metrics and traces, correlates findings with recent deployments, searches runbooks, and reports ranked root-cause hypotheses, each backed by cited evidence. A human approves every remediation before anything runs.

> **Status:** early development. The repository skeleton and design are in place; components are being built incrementally. See the [Roadmap](#roadmap) for progress.

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

For the full design, including the data model, caching, error handling, scaling, and trade-offs, see the [system design document](docs/system-design.md).

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
opspilot/
├── apps/
│   ├── api/                # FastAPI backend
│   └── worker/             # LangGraph agent worker
├── packages/
│   └── evidence/           # Deterministic Python investigation tools
├── testbed/
│   ├── scenarios/          # Incident generation scripts
│   ├── ground_truth/       # Known root causes for each scenario
│   └── snapshots/          # Frozen logs, metrics and traces
├── evals/                  # AI agent evaluation
├── infra/
│   └── docker/             # Docker Compose configuration
├── tests/
│   └── evidence/           # pytest tests for evidence tools
├── .github/
│   └── workflows/          # GitHub Actions CI pipeline
├── .env.example
├── .python-version
├── pyproject.toml
└── uv.lock
```

| Directory | Responsibility |
|---|---|
| `apps/api` | FastAPI backend: incident intake, SSE streaming, approvals, evidence lookup |
| `apps/worker` | LangGraph agent that plans and runs investigations |
| `packages/evidence` | Deterministic, read-only tools for logs, metrics, traces, deployments, and runbook RAG. Plain Python, with no LLM calls |
| `testbed/scenarios` | Scripts that inject known faults into the demo system |
| `testbed/ground_truth` | The true root cause of every injected fault, used for scoring |
| `testbed/snapshots` | Frozen telemetry so investigations can be replayed deterministically |
| `evals` | Evaluation harness and scoring |
| `infra/docker` | Docker Compose for local services (Postgres, Redis, and others) |
| `tests/evidence` | Unit tests for the evidence tools |
| `.github/workflows` | CI pipeline |

## Getting started

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

# Create your local config
cp .env.example .env

# Verify the setup
uv run pytest
```

### Running the services (planned)

These commands will work as the components land.

```bash
# Start Postgres + pgvector and Redis
docker compose -f infra/docker/docker-compose.yml up -d

# Start the API
uv run uvicorn apps.api.main:app --reload

# Start the agent worker
uv run arq apps.worker.main.WorkerSettings
```

### Running the testbed (planned)

OpsPilot is evaluated against the [OpenTelemetry Demo](https://opentelemetry.io/docs/demo/) with deliberately injected faults. Scenario scripts in `testbed/scenarios` will inject each fault and capture the resulting telemetry into `testbed/snapshots`.

## Configuration

Configuration is loaded from environment variables. Copy `.env.example` to `.env` and fill in the values. The variables below are the expected set, so check `.env.example` for the current list.

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API access |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | Langfuse tracing (cloud or self-hosted) |

Never commit `.env`. It is listed in `.gitignore`.

## API overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/incidents` | Submit an incident (`title`, `description`, optional `service`, `reported_at`, `as_of`). Returns `202` with `incident_id` and `investigation_id` |
| `GET` | `/v1/investigations/{id}` | Status, report, and evidence references |
| `GET` | `/v1/investigations/{id}/events` | Server-sent events stream of investigation progress |
| `POST` | `/v1/investigations/{id}/approval` | Approve, edit, or reject a remediation plan |
| `GET` | `/v1/evidence/{evidence_id}` | Raw evidence, so any claim in a report can be audited |
| `POST` | `/v1/webhooks/alertmanager` | Map an Alertmanager alert to an incident |

## Evaluation

OpsPilot has no real production incidents to learn from, so it makes its own:

- **Fault injection:** known faults (bad config, slow database, memory leak) are injected into the OpenTelemetry Demo, and the real logs, metrics, and traces are collected. Public datasets such as [Loghub](https://github.com/logpai/loghub) can supplement them.
- **Ground truth:** every scenario has a recorded root cause in `testbed/ground_truth`, so the agent can be scored on how often it finds it.
- **Deterministic replay:** each scenario's telemetry is frozen as a snapshot, and every evidence tool accepts an `as_of` clock override. Results are comparable across prompt and model changes.
- **Tracking:** scores are logged to Langfuse as experiment runs.

## Safety and security

- **Read-only tools.** Telemetry access uses read-only credentials.
- **Logs are untrusted input.** Log content is wrapped as quoted data and can never change tool permissions or agent behavior.
- **Redaction.** Secrets and PII are removed before data reaches the LLM.
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
- [ ] LangGraph workflow with Postgres checkpointer
- [ ] FastAPI service, job queue, and SSE streaming
- [ ] Human approval flow and audit log
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