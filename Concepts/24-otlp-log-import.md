# Importing OpenTelemetry logs

An OTLP JSON export groups log records by the resource and instrumentation scope that emitted them. OpsPilot selects the resource with `service.name=payment` and keeps timestamped warnings, errors, and fatal events with text bodies.

Severity numbers encode normalized levels. Values 13 through 16 map to warning, 17 through 20 to error, and 21 through 24 to fatal. If the number is absent or zero, the importer can use the original severity text. It prefers the event timestamp and uses the observed time when the event time is absent. The capture represents timestamps in UTC with microsecond precision.

Each normalized line points back to the original position in the export and preserves trace and span IDs for correlation. Other log attributes stay in the source export. The text body remains part of the local evidence, so use demo data or review the source for sensitive text before sharing it.

See the [OpenTelemetry Logs Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/).
