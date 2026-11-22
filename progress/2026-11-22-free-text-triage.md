# 2026-11-22 · Free-text demo triage

The incident API now accepts a title and description without a scenario ID. Deterministic service and symptom rules select the frozen replay. An optional service hint narrows the rule, and an explicit scenario continues to take precedence. Unknown or ambiguous text returns HTTP 422 before writing a job.

Verified queued Payment intake, synchronous Email routing with a service hint, and abstention on unknown or ambiguous requests. All fourteen tests and three replay evaluations passed. Routing is limited to the three demo scenarios.

See the [incident triage lesson](../Concepts/16-incident-triage.md).
