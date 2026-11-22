# 2026-11-22 · Change event correlation

The Ad and Email scenario notes record feature flag changes within gaps between Docker stats samples. Transcribed one Ad and three Email change intervals into CSV, with source-note provenance. Replay now cites the change and neighboring metric windows when the interval fits entirely in the gap. The same format can represent timestamped deployment events.

Custom capture directories can still supply metric CSVs alone. Payment remains a log-only replay because the captured warning's display time lacks a verified time zone. The Docker socket was inaccessible in the workspace, so verification used the frozen captures. Incident impact and causal attribution still need independent evidence.

See [Change events and time correlation](../Concepts/03-change-correlation.md) and the [Payment replay milestone](2026-11-22-payment-log-replay.md).
