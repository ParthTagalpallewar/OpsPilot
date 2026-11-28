# Learn OpsPilot by building it

Start with the [full project walkthrough](00-project-walkthrough.md) for an
end-to-end explanation and hands-on exercises.

Start with [Telemetry and deterministic replay](01-telemetry-and-replay.md). Run the CLI first, then trace an observation back to the CSV that produced it.
Continue with [Structured logs and evidence coverage](02-structured-logs.md) and
[Change events and time correlation](03-change-correlation.md), then run the
[replay evaluation](04-replay-evaluation.md). Next, read
[Incident intake and persistence](05-incident-api-and-persistence.md).

| Build stage | Concepts to learn |
|---|---|
| Local replay | Baselines, telemetry windows, Docker CPU and memory, evidence provenance, deterministic tests |
| Evidence collectors | Structured logs, error rates and log clustering, Prometheus counters and gauges, traces and spans, deployment correlation |
| Durable investigations | FastAPI validation, PostgreSQL transactions and migrations, Redis jobs and retries, idempotency, server-sent events |
| Runbook retrieval | Chunking, embeddings, cosine similarity, pgvector indexes, full-text search, ranking and citations |
| Agent workflow | LangGraph state and checkpoints, tool contracts, LLM hypothesis generation, citation validation and budgets |
| Approval and evaluation | Human review, dry runs, audit records, ground truth, replay, abstention and scoring |
| Shipping and operation | Docker, Kubernetes, GitHub Actions, OpenTelemetry and Langfuse |

The table follows the build order. Add a lesson with each working stage and use the corresponding implementation as the example.

Read [Human review and dry-run plans](06-human-approval.md) after the intake lesson.

Continue with [LangGraph state and routing](07-langgraph-state-and-routing.md).

Read [Runbook retrieval and BM25](08-runbook-retrieval.md) after the LangGraph lesson.

Continue with [Grounding a model explanation](09-model-grounding.md).

Read [Distributed traces and error spans](10-distributed-traces.md).

Continue with [Durable queues and worker leases](11-queues-and-leases.md).

Read [Server-sent events and reconnects](12-progress-streaming.md).

Continue with [Tracing OpsPilot with OpenTelemetry](13-opentelemetry-instrumentation.md).

Read [Alertmanager webhooks and idempotency](14-alertmanager-webhooks.md).

Continue with [Container packaging and continuous integration](15-containers-and-ci.md).

Read [Incident triage and abstention](16-incident-triage.md).

Continue with [Kubernetes workloads, services, and volumes](17-kubernetes-local-deployment.md).

Read [Prometheus range queries and capture provenance](18-prometheus-range-queries.md).

Read [Ranking hypotheses and evaluating the leading cause](19-hypothesis-ranking.md).

Continue with [Embeddings and hybrid runbook search](20-hybrid-runbook-search.md).

Read [Persistent embeddings and vector indexes](21-pgvector-persistence.md).

Continue with [Shared PostgreSQL state and transaction locks](22-postgresql-investigation-storage.md).

Read [Redis wake-up signals and durable jobs](23-redis-worker-notifications.md).

Read [Importing OpenTelemetry logs](24-otlp-log-import.md).

Read [Historical replay and look-ahead bias](25-historical-replay.md).

Read [Authentication, authorization, and approval identity](26-authenticated-approvals.md).

Read [Durable LangGraph checkpoints](27-langgraph-checkpoints.md).

Read [Evaluation traces and Langfuse](28-langfuse-evaluation-traces.md).

Read [Controlled fault experiments](29-controlled-fault-experiments.md).

Read [Alert-driven evidence collection](30-alert-driven-evidence.md).

Read [Rollout activity as incident evidence](31-kubernetes-rollout-evidence.md).

Read [Model context minimization and bounded retries](32-model-context-and-retries.md).

Read [Partial evidence and graceful degradation](33-partial-evidence.md).

Read [Measuring investigation latency](34-investigation-latency.md).

Practice following an investigation in the [debugger lab](35-debugger-lab.md).
