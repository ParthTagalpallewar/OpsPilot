"""Extract failed spans and observed parent links from saved OTLP JSON."""

import json
import re
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen

from pydantic import AliasChoices, AliasPath, BaseModel, Field

from opspilot.evidence.snapshots import publish_snapshot

MAX_TRACE_BYTES = 5_000_000


class SpanStatus(BaseModel):
    code: int | str = 0


class Span(BaseModel):
    trace_id: str = Field(alias="traceId", pattern=r"(?i)^[0-9a-f]{32}$")
    span_id: str = Field(alias="spanId", pattern=r"(?i)^[0-9a-f]{16}$")
    parent_id: str = Field(
        default="", alias="parentSpanId", pattern=r"(?i)^([0-9a-f]{16})?$"
    )
    name: str
    start: int = Field(alias="startTimeUnixNano", ge=0)
    end: int = Field(alias="endTimeUnixNano", ge=0)
    status: SpanStatus = Field(default_factory=SpanStatus)


class ScopeSpans(BaseModel):
    spans: list[Span] = Field(default_factory=list)


class Resource(BaseModel):
    attributes: list[dict] = Field(default_factory=list)


class ResourceSpans(BaseModel):
    resource: Resource = Field(default_factory=Resource)
    scopes: list[ScopeSpans] = Field(default_factory=list, alias="scopeSpans")


class TraceExport(BaseModel):
    resources: list[ResourceSpans] = Field(
        validation_alias=AliasChoices(
            "resourceSpans", AliasPath("result", "resourceSpans")
        )
    )


def read_failed_spans(
    path: Path, service: str, *, as_of: datetime | None = None
) -> list[dict]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return []

    return extract_failed_spans(raw, path, service, as_of=as_of)


def valid_trace_id(trace_id: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{32}", trace_id)) and int(trace_id, 16) != 0


def read_jaeger(base_url: str, route: str) -> bytes:
    endpoint = urlsplit(base_url)
    if (
        endpoint.scheme not in {"http", "https"}
        or not endpoint.hostname
        or endpoint.username is not None
        or endpoint.query
        or endpoint.fragment
    ):
        raise ValueError("Use a Jaeger HTTP(S) base URL without credentials or query")
    with urlopen(f"{base_url.rstrip('/')}/api/v3/{route}", timeout=15) as response:
        raw = response.read(MAX_TRACE_BYTES + 1)
    if len(raw) > MAX_TRACE_BYTES:
        raise ValueError("Jaeger response exceeded the trace capture limit")
    return raw


def discover_payment_trace(
    base_url: str, alert_time: datetime, path: Path
) -> str | None:
    start = alert_time - timedelta(minutes=10)
    query = urlencode(
        {
            "query.serviceName": "payment",
            "query.startTimeMin": start.isoformat(),
            "query.startTimeMax": alert_time.isoformat(),
            "query.searchDepth": 20,
        }
    )
    try:
        raw = read_jaeger(base_url, f"traces?{query}")
    except HTTPError as exc:
        if exc.code != 404:
            raise
        with exc:
            try:
                details = json.loads(exc.read(4096))
            except ValueError:
                raise exc from None
        if details == {"error": {"httpCode": 404, "message": "No traces found"}}:
            return None
        raise
    candidates = set()
    for chunk in raw.splitlines():
        if not chunk.strip():
            continue
        spans = extract_failed_spans(
            chunk, path, "payment", as_of=alert_time, started_after=start
        )
        candidates.update(span["trace_id"] for span in spans)
    return min(candidates, default=None)


def capture_payment_trace(base_url: str, trace_id: str, directory: Path) -> Path:
    if not valid_trace_id(trace_id):
        raise ValueError("Use a nonzero 32-character hexadecimal Jaeger trace ID")
    trace_id = trace_id.lower()
    raw = read_jaeger(base_url, f"traces/{trace_id}")
    path = directory / "payment-traces.json"
    spans = extract_failed_spans(raw, path, "payment")
    if not spans or any(span["trace_id"] != trace_id for span in spans):
        raise ValueError("The export must contain a failed Payment span for this trace")
    publish_snapshot(path, raw)
    return path


def epoch_nanoseconds(value: datetime) -> int:
    elapsed = value - datetime(1970, 1, 1, tzinfo=UTC)
    return (
        elapsed.days * 86400 + elapsed.seconds
    ) * 1_000_000_000 + elapsed.microseconds * 1000


def extract_failed_spans(
    raw: bytes,
    path: Path,
    service: str,
    *,
    as_of: datetime | None = None,
    started_after: datetime | None = None,
) -> list[dict]:
    try:
        export = TraceExport.model_validate_json(raw)
    except ValueError as exc:
        raise ValueError(f"{path}: invalid OTLP JSON trace export") from exc

    cutoff_ns = epoch_nanoseconds(as_of) if as_of is not None else None
    start_ns = epoch_nanoseconds(started_after) if started_after is not None else None
    spans = {}
    for resource in export.resources:
        name = next(
            (
                item.get("value", {}).get("stringValue")
                for item in resource.resource.attributes
                if item.get("key") == "service.name"
                and isinstance(item.get("value"), dict)
            ),
            None,
        )
        for scope in resource.scopes:
            for span in scope.spans:
                key = (span.trace_id.lower(), span.span_id.lower())
                if span.end < span.start or key in spans:
                    raise ValueError(f"{path}: invalid duration or duplicate span ID")
                if cutoff_ns is None or span.end <= cutoff_ns:
                    spans[key] = (name, span)

    evidence = []
    for (trace_id, span_id), (name, span) in sorted(spans.items()):
        if name != service or span.status.code not in (2, "STATUS_CODE_ERROR"):
            continue
        if start_ns is not None and span.start < start_ns:
            continue
        parent_id = span.parent_id.lower()
        parent = spans.get((trace_id, parent_id))
        evidence.append(
            {
                "id": f"ev_trace_{trace_id}_{span_id}",
                "type": "trace_error",
                "source": path.name,
                "trace_id": trace_id,
                "span_id": span_id,
                "service": service,
                "operation": span.name,
                "duration_ms": (span.end - span.start) / 1_000_000,
                "parent_span_id": parent_id or None,
                "parent_service": parent[0] if parent else None,
                "parent_operation": parent[1].name if parent else None,
            }
        )
    return evidence


def correlate_log_spans(logs: list[dict], traces: list[dict]) -> list[dict]:
    by_span = {(trace["trace_id"], trace["span_id"]): trace for trace in traces}
    observations = []
    for cluster in logs:
        matches = defaultdict(list)
        for record in cluster["records"]:
            key = (record.get("trace_id"), record.get("span_id"))
            trace = by_span.get(key)
            if trace:
                matches[trace["id"]].append(record["line"])
        for evidence_id, lines in matches.items():
            locations = ", ".join(map(str, lines))
            observations.append(
                {
                    "statement": (
                        f"Payment log lines {locations} share both trace and span IDs "
                        "with the captured failed span."
                    ),
                    "evidence_ids": [cluster["id"], evidence_id],
                }
            )
    return observations
