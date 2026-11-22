# Evaluation traces and Langfuse

OpsPilot traces one evaluation run and a child span for each scenario. Each scenario span contains the pass/fail checks, number of resolved claims, and a hash of the reference dataset. The hash tells you whether two runs used the same expected outputs without including the full dataset in the span.

An OTLP HTTP exporter can send those spans to Langfuse, where the scenario spans are marked as evaluator observations. The evaluation span contains numeric and boolean outcomes. The source logs, raw reports, and reference labels stay local.

A trace answers which steps ran and how long they took. An evaluation answers whether the results matched a reference. Looking at both helps narrow a regression to a collector, retrieval change, or ranking rule.

## Practice

Run `OPSPILOT_TRACING=console uv run opspilot eval`. Find the Payment evaluator span and connect it to the replay spans using the trace IDs and parent IDs. Compare its hypothesis check with the Ad leading-cause check.

See the [Langfuse OpenTelemetry guide](https://langfuse.com/integrations/native/opentelemetry).
