# Partial evidence and graceful degradation

Evidence sources can fail independently. If a saved trace is invalid but its warning log and request counts are readable, OpsPilot still reports the warning and measured failure rate. It marks coverage as partial and labels the failed source. Correlation needs both signals, so the report omits log-to-span links in that case.

The report distinguishes an optional source that was never captured from a captured source that failed to load. A missing required resource window leaves the other window available as evidence. A comparison needs both windows. If change evidence fails validation, a resource report can describe the measurements while withholding a named change hypothesis.

## Practice

Copy the Checkout capture to a temporary directory and corrupt only the trace file. Compare the resulting report with the original. Find the claims that remain and explain what additional data would restore the missing correlation.

## Runbook search fallback

Hybrid search combines independent keyword and vector rankings. If the vector backend is unavailable, OpsPilot can cite the keyword result and label it `keyword_fallback`. If both backends fail, the graph returns its telemetry findings with an empty guidance list. Retrieval coverage and metric evidence are separate parts of the report.
