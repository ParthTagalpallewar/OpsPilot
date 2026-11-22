# Grounding a model explanation

OpsPilot first runs deterministic collectors, computes the baseline comparison, retrieves runbook guidance, and validates citations. The optional model step receives the existing hypothesis, the aggregate measurements, the change intervals, and the retrieved runbook section. This is a retrieval-augmented generation flow because retrieved material becomes part of the model's context.

The application requests an explanation with a statement and evidence IDs. It parses the candidate against a schema and requires a measured metric citation. A schema check catches malformed responses. A citation check catches invented IDs. To verify the claim itself, an operator still needs to read the measurements and decide whether they support its wording.

The deterministic hypothesis remains in the report when the provider is unavailable or the response fails validation. Payment has no deterministic hypothesis, so the graph withholds an explanation without calling the provider. One call per run, a bounded input, a request timeout, and a maximum output token count help control latency and cost.

## Practice

Run the standard replay and find the evidence IDs that support the Ad hypothesis. Then run with `--with-claude` using the README configuration, or read the mocked-response test. Compare the deterministic hypothesis with the optional explanation and check whether each cited record supports the statement.
