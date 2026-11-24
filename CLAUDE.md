# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

OpsPilot replays captured incident telemetry through a LangGraph workflow and produces a report in which every claim cites evidence IDs. Evidence collection, correlation, and hypothesis ranking are deterministic Python; the only LLM call is an optional explanation (`--with-claude`). Remediation is a dry-run plan that a human must approve.

The README's "Target architecture" and agent-graph diagrams (plan loops, LLM hypothesize step) describe the goal, not the code. The implemented graph is described below.

## Commands

Run from the repository root. Python 3.12 is pinned; dependencies are managed with `uv`.

```bash
uv sync                                   # add --extra postgres / redis / semantic as needed
uv run ruff check .                       # CI also runs: uv run ruff format --check .
uv run pytest                             # all tests
uv run pytest tests/test_queue.py::test_expired_worker_cannot_overwrite_reclaimed_job
uv run opspilot eval                      # baseline scenarios; exit 1 on any failure
uv run opspilot eval --ground-truth testbed/ground_truth/extended.json
uv run opspilot replay ad-high-cpu        # also: email-memory-leak, payment-failure
uv run opspilot replay payment-failure --captures testbed/captures/checkout-payment
uv run uvicorn opspilot.apps.api.main:local_app --factory   # API (SQLite by default)
uv run python -m opspilot.apps.worker.main                  # queue worker (--once for one job)
```

CI (`.github/workflows/ci.yml`) runs lint, format check, pytest, both evals, and a Compose smoke test (`infra/docker/smoke_replay.py`) against SQLite and against the PostgreSQL + Redis overlay. There are no local PostgreSQL tests; the container smoke job is the only coverage of that path.

## Architecture

**Replay graph** (`opspilot/replay.py`): `START → collect_resources | collect_payment → report_resources | report_payment → retrieve_runbook → validate → [reason] → END`. The route is chosen by scenario: `ad-high-cpu` and `email-memory-leak` are resource scenarios (`METRIC_SCENARIOS`), `payment-failure` is the trace/log scenario. `reason` runs only with `with_claude`.

**Evidence records** are plain dicts with a deterministic `id` (for example `ev_ad_fault_all`, `ev_log_<sha256>`, `ev_trace_<trace>_<span>`). Observations, guidance, and hypotheses each carry `evidence_ids`; `validate_report` rejects duplicate IDs or any claim whose citations do not resolve. `opspilot/evaluation.py` scores reports against `testbed/ground_truth/*.json` using the same citation rules.

**Collectors** (`opspilot/evidence/`) read capture files by fixed names inside a captures directory: `{service}-stats-{baseline,fault}.csv` or `{service}-prometheus.json`, `{service}-changes.csv`, `{service}-rollouts.csv`, `payment-traces.json`, `payment-logs.jsonl`, `payment-requests.json`, `payment-prometheus.json`, plus `*-collection.json` status files written by live capture. A missing optional file is skipped; an unreadable or invalid one becomes a `source_issues` entry and marks the report `coverage: partial`. Every collector honors an `as_of` cutoff; runbook retrieval is skipped when `as_of` is set.

**Runbooks** are resolved at `<captures>/../runbooks`, so only `testbed/scenarios` replays get runbook guidance. `opspilot/model_context.py` sends a runbook section to Claude only if the SHA-256 of its heading and excerpt is in `REVIEWED_RUNBOOKS`; editing a section in `testbed/runbooks/` silently drops it from the model context until the hash is updated.

**Hypotheses** (`opspilot/hypotheses.py`) are ranked by code: a change is a rank-1 candidate only if it falls between the baseline and the first fault window, and only when every fault window's mean exceeds the baseline peak. Confidence is always `low`. A tie between rank-1 candidates makes the report choose the cause-free hypothesis (abstention), which the extended eval checks.

**Persistence** (`opspilot/investigations.py`, `opspilot/storage.py`): `InvestigationStore` takes a `Path` (SQLite) or a `str` DSN (PostgreSQL); SQL is written with `?` placeholders and rewritten to `%s` for psycopg. Tables are created, and migrated with inline `ALTER`s, in the store constructor. Write sessions serialize with `BEGIN IMMEDIATE` (SQLite) or a transaction advisory lock (PostgreSQL). Queued jobs live in `replay_jobs` with a `claim_token` and a 60-second lease; a worker whose token no longer matches has its result discarded, and a job claimed `MAX_JOB_ATTEMPTS` times without finishing is marked failed. PostgreSQL workers also checkpoint the replay graph (`opspilot/checkpoints.py`) and resume reclaimed jobs.

**Approvals** (`opspilot/approvals.py`, `opspilot/approval_graph.py`): a plan is hashed and expires after `PLAN_TTL`; a review must echo `plan_id` and `plan_hash`. Decisions are appended to `approval_events` and folded into the document on read. On PostgreSQL each plan also waits on a LangGraph `interrupt`; on SQLite it does not.

**Worker** (`opspilot/apps/worker/main.py`): `serve()` logs unexpected exceptions and keeps polling, leaving the claimed job to its lease; SIGTERM finishes the current job, then exits.

**Markdown summary** (`opspilot/summary.py`): `render_markdown` backs `opspilot replay --format markdown` and `GET /v1/investigations/{id}/summary`. Pass any text that can come from telemetry, the incident, or the model through `text()`, which escapes Markdown and keeps it on one line.

**Live capture** (`opspilot/live_metrics.py`, `opspilot/live_traces.py`) runs in the worker for Alertmanager alerts labeled `opspilot_mode: live`, writes a per-investigation snapshot under `OPSPILOT_LIVE_CAPTURES`, then replays it like any capture. `publish_snapshot` writes via hard link and never overwrites; `FileExistsError` is treated as "another attempt already wrote it".

## Conventions

- Configuration comes only from environment variables (`OPSPILOT_*`, `ANTHROPIC_API_KEY`, `LANGFUSE_*`); there is no `.env` loader.
- Telemetry, log text, and runbook text are untrusted input: collectors validate shape strictly, and nothing from them reaches the model except allowlisted fields in `model_context.py`.
- Tests use the real fixtures in `testbed/`, temporary SQLite databases (`tmp_path`), and `httpx.ASGITransport` against `create_app`. Changes to report contents usually need matching updates to `testbed/ground_truth/` and the eval must still pass.
- `Concepts/` holds teaching notes and `progress/` holds dated development logs; add to them when introducing a new concept or verifying new behavior.
