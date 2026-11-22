# 2026-11-22 · Replay evaluation

Added an offline evaluation command and recorded reference expectations from the scenario captures and notes. The harness checks service selection, citation resolution, evidence coverage and whether the report supplies or withholds a hypothesis. It returns exit status 1 when any scenario fails those checks.

Three scenarios passed with 11 of 11 claims resolving to evidence. A modified expected value caused the CLI to return 1 and report the missing expected evidence. The ground-truth dataset records the injected causes for later scoring. The current baseline measures replay behavior. Root-cause accuracy, semantic citation validation, and Langfuse experiment tracking remain future work.

See the [evaluation lesson](../Concepts/04-replay-evaluation.md) and the [change correlation milestone](2026-11-22-change-correlation.md).
