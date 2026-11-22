# 2026-11-22 · Payment log replay

Extended the offline CLI with a third scenario using a warning excerpt transcribed from the Payment scenario notes. The fixture preserves the display timestamp and error text prefix. The fixture omits the user-context attribute and uses the notes as the provenance record.

The new log reader validates structured records and groups service warnings and errors by exact message. Evidence includes a repeatable cluster ID and the source line for each matching record. The report leaves the hypothesis unset because the recorded excerpt gives only the symptom.

Read the [structured logs lesson](../Concepts/02-structured-logs.md) alongside the replay. See the [previous milestone](2026-11-22-metrics-replay.md) for the Ad and Email captures.

Remaining Payment evidence includes a verified time zone, a full request capture with failure and total counts, a trace through Checkout and Payment, and timestamped change events.
