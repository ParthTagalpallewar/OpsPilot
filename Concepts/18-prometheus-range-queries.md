# Prometheus range queries and capture provenance

A range query evaluates an expression at regular steps between two timestamps. OpsPilot requests one series over a baseline window and again over a later incident window. Use the same percentage expression and aggregate dimensions in both requests. For counters such as cumulative CPU seconds, compute a rate first and then convert to the intended unit.

The capture stores the original responses, query, step, and requested windows. Replay reads the samples without contacting Prometheus. Each evidence record identifies the query and labels. A missing series, several series, or a label change makes the comparison ambiguous, so capture rejects those responses.

The project’s resource summaries expect percentages. For example, if your CPU query returns logical cores, multiply it by 100 so one full core equals 100%. The capture validates numeric values. Selecting a query with the right physical meaning remains the operator's responsibility.

See the [Prometheus range query reference](https://prometheus.io/docs/prometheus/latest/querying/api/#range-queries).
