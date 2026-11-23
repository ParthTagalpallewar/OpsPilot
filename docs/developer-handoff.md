# OpsPilot developer handoff

Current as of November 23, 2026. Share this file with the repository checkout
that contains it. The earlier baseline commit, `2afcd4e`, predates the live
evidence, extended test suite, and learning material described here. Run
`git log -1 --oneline` and `git status --short` to identify the exact checkout
when handing off further work.

## Product and scope

OpsPilot is a résumé project for evidence-backed SRE incident investigation.
It accepts incidents or Alertmanager notifications, builds a cited report,
streams status, and supports authenticated approval of dry-run plans.
The user plans to learn the current design first and then take ownership of
Kubernetes and live deployment work. Start with the [learning walkthrough](../Concepts/00-project-walkthrough.md)
and [portfolio demo](portfolio-demo.md). The original product brief and system
design are in `projectDescription.txt` and `systemDesign.txt` in the parent
workspace directory.

## Run and verify locally

Run from the Git repository root.

```sh
uv sync
uv run ruff check
uv run pytest
uv run opspilot eval
uv run opspilot eval --ground-truth testbed/ground_truth/extended.json
uv run opspilot replay payment-failure --captures testbed/captures/checkout-payment
```

The default CLI replay uses local fixtures. The local API uses SQLite unless
configured otherwise. To test the packaged API, queue, worker, evidence,
and approval flow together, run the Compose demo and its smoke script.
The [README](../README.md#run-the-postgresql-and-redis-demo) also documents
the shared Compose overlay with PostgreSQL and Redis.

## Source map

| Area | Files and responsibilities |
|---|---|
| Intake and API | [FastAPI routes](../opspilot/apps/api/main.py), [alert mapping](../opspilot/apps/api/alertmanager.py), [triage](../opspilot/triage.py), and [role checks](../opspilot/apps/api/auth.py). |
| Jobs and persistence | [InvestigationStore](../opspilot/investigations.py) owns durable jobs, leases, report storage, and progress records. [Storage](../opspilot/storage.py) selects SQLite or PostgreSQL. [Redis wake-up](../opspilot/wakeup.py) signals available jobs. |
| Workflow | [Replay graph](../opspilot/replay.py) branches into resource or Payment analysis, adds runbook guidance, validates citations, and can request a model explanation. [Checkpoints](../opspilot/checkpoints.py) support PostgreSQL recovery. |
| Live evidence | [Resource capture](../opspilot/live_metrics.py) fetches Prometheus windows. [Payment capture](../opspilot/live_traces.py) uses Jaeger and can add local OTLP log and Prometheus evidence. See [collectors](../opspilot/evidence/) for evidence parsing and frozen files. |
| Review | [Approvals](../opspilot/approvals.py) and [review graph](../opspilot/approval_graph.py) bind decisions to the reviewed plan and provide audit history and dry-run previews. |
| Verification | [Tests](../tests/), [ground truth](../testbed/ground_truth/), [captured evidence](../testbed/captures/), and [container smoke test](../infra/docker/smoke_replay.py). |
| Deployment and operations | [Docker infrastructure](../infra/docker/), [Kubernetes resources](../infra/kubernetes/), [CI](../.github/workflows/ci.yml), and [operational metrics](../opspilot/operational_metrics.py). |

## What has been verified

| Path | Evidence and boundary |
|---|---|
| Local deterministic replay | Baseline Ad CPU, Email memory, and Payment scenarios plus four extended cases exercise citations, time cutoffs, healthy and ambiguous cases, and Checkout-to-Payment log and trace links. |
| Payment fault data | A controlled Checkout experiment recorded six successful and six failed requests. The saved warning and server span IDs match. The [capture notes](../testbed/captures/checkout-payment/README.md) describe the experiment. |
| Trace discovery | A real temporary Jaeger accepted the scrubbed fixture over OTLP. The worker found a failed Payment trace and linked its warning after receiving an alert without a trace ID. [Verification notes](../progress/2026-11-23-live-payment-trace-discovery.md) |
| Alertmanager and live Prometheus | A manually seeded alert made Alertmanager deliver an authenticated webhook. The worker completed with live rate evidence and partial coverage because Jaeger found no matching failure. [Smoke test notes](../progress/2026-11-23-alertmanager-prometheus-smoke.md) |
| Kubernetes | An existing local manifest packages API and worker in one Pod with a SQLite PVC. Cluster rollout and volume provisioning require verification. [Kubernetes progress note](../progress/2026-11-22-kubernetes-demo.md) |

## Continue from here

1. **Verify the existing Kubernetes demo locally.** Use the [kind walkthrough](../README.md#run-on-a-local-kubernetes-cluster).
   Confirm the image loads, PVC binds, API is ready, and the smoke test passes
   through port forwarding. Replace the Pod and confirm the prior investigation
   can still be retrieved.
2. **Deploy shared state.** Use the [Compose overlay](../infra/docker/shared.compose.yml)
   as a reference for configuring PostgreSQL and Redis. Run API and worker as
   separate workloads and verify that both use the same database and capture
   paths. PostgreSQL stores jobs, reports, and checkpoints. Relay Redis
   notifications and confirm job recovery by stopping a worker mid-run.
   If live capture is enabled, verify replacement workers can access the
   per-investigation snapshot directory.
3. **Configure a hosted environment.** Publish a versioned image and
   configure the API Service, ingress and TLS, and credentials. Pass
   database and Redis connection settings and webhook credentials securely.
   Verify authenticated webhook delivery, report retrieval, and approval
   access over the deployed endpoint. Decide how to provide and back up
   PostgreSQL and capture storage before relying on the environment for demos.
4. **Close the full live Payment gap.** In an isolated OpenTelemetry Demo,
   induce a controlled Payment failure. Let a Prometheus rule fire through
   Alertmanager and verify a single report links live metrics, a failed
   Payment trace, and its matching warning. Confirm repeated webhook delivery
   maps to the same investigation. Coordinate this with the deployment work
   if the alert sender and collector need stable addresses.
5. **Track work beyond the first deployment.** Live Kubernetes rollout
   collection and correlation, remote log-store queries, and broader live
   model evaluation remain follow-ups. Record verified behavior in
   [progress](../progress/) and teach new concepts in [Concepts](../Concepts/).

## Configuration to carry between environments

- **Storage** uses `OPSPILOT_DATABASE_DSN` in shared mode and `OPSPILOT_DB`
  for SQLite. API and worker must agree. Configure Redis using the
  [README settings](../README.md#enable-redis-worker-notifications).
- **Evidence** uses `OPSPILOT_CAPTURES` for replay inputs and
  `OPSPILOT_LIVE_CAPTURES` for saved live snapshots. Configure Jaeger and
  Prometheus using the [live capture settings](../README.md#capture-fresh-metrics-from-an-alert).
- **Access** uses `OPSPILOT_API_CREDENTIALS` for the credentials file in
  authenticated mode. Use role-specific credentials for webhook, operator,
  and reviewer. See the [README access setup](../README.md#configure-authenticated-api-access).
