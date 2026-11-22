"""Group warning and error events from a structured log capture."""

import json
import re
from collections import defaultdict
from datetime import datetime
from hashlib import sha256
from pathlib import Path

FAILURE_SEVERITIES = {"warn", "error", "fatal"}


def summarize_logs(
    path: Path, service: str, *, as_of: datetime | None = None
) -> list[dict]:
    groups = defaultdict(list)
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError
                fields = ("service", "severity", "timestamp", "message", "origin")
                if any(
                    not isinstance(row.get(field), str) or not row[field].strip()
                    for field in fields
                ):
                    raise ValueError
                timestamp = datetime.fromisoformat(row["timestamp"])
                identifiers = {}
                for field, size in (("trace_id", 32), ("span_id", 16)):
                    value = row.get(field)
                    if value is None or value == "":
                        continue
                    if (
                        not isinstance(value, str)
                        or len(value) != size
                        or not re.fullmatch(r"[0-9a-fA-F]+", value)
                        or int(value, 16) == 0
                    ):
                        raise ValueError
                    identifiers[field] = value.lower()
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: invalid log record") from exc

            if as_of is not None and (
                timestamp.utcoffset() is None or timestamp > as_of
            ):
                continue
            severity = row["severity"].strip().lower()
            if severity == "warning":
                severity = "warn"
            if row["service"] == service and severity in FAILURE_SEVERITIES:
                groups[(severity, row["message"].strip())].append(
                    {
                        "line": line_number,
                        "timestamp": row["timestamp"],
                        "origin": row["origin"],
                        **identifiers,
                    }
                )

    evidence = []
    for (severity, message), records in sorted(groups.items()):
        signature = json.dumps([service, severity, message]).encode()
        evidence.append(
            {
                "id": f"ev_log_{sha256(signature).hexdigest()}",
                "type": "log_cluster",
                "source": path.name,
                "service": service,
                "severity": severity,
                "message": message,
                "count": len(records),
                "records": records,
            }
        )
    return evidence
