# 2026-11-22 · Prometheus capture and replay

Added a read-only CLI collector that freezes two non-overlapping Prometheus range-query results in one file. It checks both responses before publishing the capture and preserves the existing file on repeat attempts. The graph uses the same baseline and incident summary logic as Docker CSV replay and attaches the source query and series labels. Model explanations are disabled for these captures.

Verified the collector and replay together using mocked Prometheus HTTP responses. The three golden replay cases continue to use their existing fixtures. A live query against the demo Prometheus instance remains unverified.

See the [Prometheus range query lesson](../Concepts/18-prometheus-range-queries.md).
