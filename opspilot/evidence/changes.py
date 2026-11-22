"""Replay change events whose exact time may be uncertain."""

import csv
from datetime import UTC, datetime
from pathlib import Path

CHANGE_FIELDS = ("kind", "name", "value", "earliest", "latest", "origin")


def read_changes(
    path: Path, service: str, *, as_of: datetime | None = None
) -> list[dict]:
    try:
        stream = path.open(encoding="utf-8", newline="")
    except FileNotFoundError:
        return []

    evidence = []
    with stream:
        rows = csv.DictReader(stream)
        if not set(CHANGE_FIELDS).issubset(rows.fieldnames or ()):
            raise ValueError(f"{path}: missing change event columns")
        for row in rows:
            try:
                event = {field: (row[field] or "").strip() for field in CHANGE_FIELDS}
                if not all(event.values()):
                    raise ValueError
                earliest = datetime.fromisoformat(event["earliest"])
                latest = datetime.fromisoformat(event["latest"])
                if earliest.utcoffset() is None or latest.utcoffset() is None:
                    raise ValueError
                if earliest > latest:
                    raise ValueError
            except ValueError as exc:
                raise ValueError(
                    f"{path}:{rows.line_num}: invalid change event"
                ) from exc

            if as_of is not None and latest > as_of:
                continue
            evidence.append(
                {
                    **event,
                    "id": f"ev_change_{service}_{rows.line_num}",
                    "type": "change_event",
                    "service": service,
                    "source": path.name,
                    "line": rows.line_num,
                    "earliest": earliest.astimezone(UTC).isoformat(),
                    "latest": latest.astimezone(UTC).isoformat(),
                }
            )
    return evidence


def correlate_changes(windows: list[dict], changes: list[dict]) -> list[dict]:
    observations = []
    for before, after in zip(windows, windows[1:], strict=False):
        end = datetime.fromisoformat(before["end"])
        start = datetime.fromisoformat(after["start"])
        for change in changes:
            earliest = datetime.fromisoformat(change["earliest"])
            latest = datetime.fromisoformat(change["latest"])
            if end <= earliest <= latest <= start:
                observations.append(
                    {
                        "statement": (
                            f"The documented interval for {change['name']} changing to "
                            f"{change['value']} falls between the last reading of "
                            f"{before['phase']} ({before['variant']}) and the first "
                            f"reading of {after['phase']} ({after['variant']})."
                        ),
                        "evidence_ids": [before["id"], change["id"], after["id"]],
                    }
                )
    return observations
