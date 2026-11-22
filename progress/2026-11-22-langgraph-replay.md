# 2026-11-22 · LangGraph replay workflow

Moved replay behind a shared compiled LangGraph workflow. State carries the scenario, capture path, tool outputs, and final report. A conditional edge selects the relevant collectors. Both report paths converge at a citation validation node that rejects missing, unresolved, or duplicate evidence IDs.

The CLI, evaluation harness, and API all use this graph. The current branches use deterministic analysis. Model reasoning, runbook retrieval, durable checkpoints, and approval resumption remain pending.

See the [LangGraph lesson](../Concepts/07-langgraph-state-and-routing.md) and the [human approval milestone](2026-11-22-human-approval.md).
