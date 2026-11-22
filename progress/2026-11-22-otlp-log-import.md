# 2026-11-22 · OTLP Payment log import

Added a CLI importer that freezes timestamped Payment warnings and errors from an OTLP JSON export. It maps severity, normalizes timestamps and identifiers, preserves source positions, and omits arbitrary attributes. The output feeds the existing Payment replay and exact trace/span correlation.

Verified the import and replay using a controlled OTLP fixture with Payment and Checkout records, a warning and an info event, and observed-time fallback. The test also verifies that repeat imports cannot replace the frozen output. A live OpenTelemetry Demo log export remains unverified.

See the [OTLP log import lesson](../Concepts/24-otlp-log-import.md).
