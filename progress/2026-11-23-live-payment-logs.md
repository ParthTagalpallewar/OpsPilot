# 2026-11-23 · Live Payment warning capture

Added optional trace-filtered log collection for live Payment investigations. It reads JSON or newline-delimited OTLP from the collector file exporter, keeps only warnings for the selected trace, and freezes the normalized capture. If the export is unavailable or the warning has yet to arrive, the saved capture records that gap and replay preserves its Jaeger evidence.

Verified filtering and correlation against the actual collector export from the Checkout experiment. Regression tests cover JSONL origins, reusing a snapshot, and partial reports when the file is missing. The implementation reads a bounded local export. Remote log-store queries and waiting for delayed logs remain pending.

See the [alert-driven evidence lesson](../Concepts/30-alert-driven-evidence.md).
