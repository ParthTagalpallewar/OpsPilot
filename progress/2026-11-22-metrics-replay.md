# 2026-11-22 · Captured metrics replay

The existing project notes specify evidence-first incident investigation and a replayable OpenTelemetry testbed. The repository already contained Ad and Email Docker stats captures and a small error-rate helper.

- Added `opspilot replay` for the two captured resource scenarios.
- Summarized baseline and fault windows with source filenames, timestamps and evidence IDs.
- Kept each Email fault variant separate and ordered results by capture time.
- Added a resource pressure hypothesis based on baseline comparison.
- Started the learning sequence in [Concepts](../Concepts/README.md).

This milestone uses an offline, deterministic CLI and the checked-in captures. Payment still needs machine-readable telemetry for replay. Upcoming implementation includes log and trace evidence, deployment events, runbook retrieval, LangGraph, the API and approval flow, evaluation, and deployment.

| Scenario | Comparison |
|---|---|
| Ad | 0.74% baseline mean CPU → 398.00% fault mean CPU |
| Email | 61.61% baseline mean memory → 68.61%, 85.99%, and 84.19% for successive variants |
