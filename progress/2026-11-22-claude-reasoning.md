# 2026-11-22 · Optional Claude explanation

Added a LangGraph node that requests a tentative explanation for an existing deterministic hypothesis. The CLI opts in with `--with-claude` for the repository demo captures. The provider receives aggregate evidence and retrieved runbook context. The node checks the response schema, citation IDs and presence of a metric citation before attaching the explanation.

The default replay, evaluation, and API remain offline. Payment skips the provider because its log excerpt does not support a hypothesis. Invalid responses and provider errors produce a status while preserving the baseline report. Mocked provider checks cover valid output, fabricated citations, and Payment abstention. A live provider call and semantic scoring remain unverified.

See the [model grounding lesson](../Concepts/09-model-grounding.md) and the [runbook retrieval milestone](2026-11-22-runbook-retrieval.md).
