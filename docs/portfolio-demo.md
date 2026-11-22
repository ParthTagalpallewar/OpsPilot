# OpsPilot portfolio demo

OpsPilot turns an incident report into a cited investigation. The Ad replay makes the evidence chain easy to follow.

1. Start the API and worker using the [Docker quickstart](../README.md#run-the-packaged-demo).
2. Run `python3 infra/docker/smoke_replay.py`. It queues Ad CPU, checks graph progress and a cited record, edits the proposed follow-up, and approves the updated dry-run plan.
3. Open the investigation in the API docs using the ID printed by the smoke script. Follow the leading hypothesis to the baseline, first fault window, and feature flag interval.
4. Compare the Payment replay. The saved warning establishes a failure symptom. The report withholds a cause when the capture lacks corroboration.
5. Run `uv run opspilot eval`. Explain that the three scenarios are regression fixtures and that two have enough evidence for leading-cause scoring.

## Resume bullets

- Built an incident investigation service with FastAPI and LangGraph that correlates OpenTelemetry Demo metrics, log warnings, traces, and change events into evidence-linked hypotheses.
- Implemented durable investigation jobs, resumable progress streams, PostgreSQL checkpoints, and reviewer-attributed dry-run approvals. Verified worker recovery after a forced exit.
- Added hybrid runbook retrieval with BM25, BGE-small embeddings, and pgvector, plus a repeatable evaluator. All three frozen scenarios passed, including two labeled leading-cause checks and Payment abstention.
