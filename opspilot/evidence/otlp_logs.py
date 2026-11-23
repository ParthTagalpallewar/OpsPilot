"""Normalize exported OTLP JSON log records into frozen Payment evidence."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, Field

from opspilot.evidence.logs import FAILURE_SEVERITIES
from opspilot.evidence.snapshots import publish_snapshot
from opspilot.evidence.traces import Resource

MAX_EXPORT_BYTES = 10_000_000
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class LogRecord(BaseModel):
    time: int = Field(default=0, alias="timeUnixNano", ge=0, lt=2**64)
    observed: int = Field(default=0, alias="observedTimeUnixNano", ge=0, lt=2**64)
    severity_number: int = Field(default=0, alias="severityNumber", ge=0, le=24)
    severity_text: str = Field(default="", alias="severityText")
    body: dict = Field(default_factory=dict)
    trace_id: str = Field(default="", alias="traceId", pattern=r"(?i)^([0-9a-f]{32})?$")
    span_id: str = Field(default="", alias="spanId", pattern=r"(?i)^([0-9a-f]{16})?$")

    def severity(self) -> str:
        if self.severity_number >= 21:
            return "fatal"
        if self.severity_number >= 17:
            return "error"
        if self.severity_number >= 13:
            return "warn"
        if self.severity_number:
            return ""
        text = self.severity_text.strip().lower()
        return "warn" if text == "warning" else text


class ScopeLogs(BaseModel):
    records: list[LogRecord] = Field(default_factory=list, alias="logRecords")


class ResourceLogs(BaseModel):
    resource: Resource = Field(default_factory=Resource)
    scopes: list[ScopeLogs] = Field(default_factory=list, alias="scopeLogs")


class LogExport(BaseModel):
    resources: list[ResourceLogs] = Field(alias="resourceLogs")


class NoMatchingPaymentLogs(ValueError):
    pass


def import_payment_logs(
    source: Path, directory: Path, *, trace_id: str | None = None
) -> Path:
    with source.open("rb") as stream:
        content = stream.read(MAX_EXPORT_BYTES + 1)
    if len(content) > MAX_EXPORT_BYTES:
        raise ValueError("OTLP log export exceeded the capture limit")
    rows = []
    try:
        if source.suffix == ".jsonl":
            for line_number, line in enumerate(content.splitlines(), start=1):
                if line.strip():
                    export = LogExport.model_validate_json(line)
                    rows.extend(
                        normalize(export, f"{source.name}:{line_number}", trace_id)
                    )
        else:
            export = LogExport.model_validate_json(content)
            rows.extend(normalize(export, source.name, trace_id))
    except ValueError as exc:
        raise ValueError(f"{source}: invalid OTLP JSON log export") from exc

    if not rows:
        raise NoMatchingPaymentLogs(
            "No matching timestamped Payment warnings or errors"
        )
    path = directory / "payment-logs.jsonl"
    publish_snapshot(path, ("\n".join(rows) + "\n").encode())
    return path


def normalize(export: LogExport, origin: str, trace_id: str | None) -> list[str]:
    rows = []
    for resource_index, resource in enumerate(export.resources):
        if not any(
            attribute.get("key") == "service.name"
            and attribute.get("value") == {"stringValue": "payment"}
            for attribute in resource.resource.attributes
        ):
            continue
        for scope_index, scope in enumerate(resource.scopes):
            for log_index, log in enumerate(scope.records):
                severity = log.severity()
                message = log.body.get("stringValue")
                timestamp = log.time or log.observed
                if (
                    (trace_id is not None and log.trace_id.lower() != trace_id)
                    or severity not in FAILURE_SEVERITIES
                    or not isinstance(message, str)
                    or not message.strip()
                    or not timestamp
                ):
                    continue
                row = {
                    "service": "payment",
                    "severity": severity,
                    "timestamp": (
                        EPOCH + timedelta(microseconds=timestamp // 1000)
                    ).isoformat(),
                    "message": message.strip(),
                    "origin": (
                        f"{origin}#/resourceLogs/{resource_index}"
                        f"/scopeLogs/{scope_index}/logRecords/{log_index}"
                    ),
                }
                for field, value in (
                    ("trace_id", log.trace_id),
                    ("span_id", log.span_id),
                ):
                    if value and int(value, 16):
                        row[field] = value.lower()
                rows.append(json.dumps(row))

    return rows
