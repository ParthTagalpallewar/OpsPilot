"""Deterministic summaries of captured Docker stats."""

import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean


def summarize_capture(
    path: Path, metric: str, service: str, phase: str, *, as_of: datetime | None = None
) -> list[dict]:
    groups = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream)
        if not {"timestamp_utc", metric}.issubset(rows.fieldnames or ()):
            raise ValueError(f"{path}: missing timestamp_utc or {metric} column")
        for row in rows:
            try:
                timestamp = datetime.fromisoformat(row["timestamp_utc"])
                raw_value = row[metric]
                if timestamp.utcoffset() is None or not raw_value.endswith("%"):
                    raise ValueError
                value = float(raw_value.removesuffix("%"))
                if not math.isfinite(value) or value < 0:
                    raise ValueError
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{rows.line_num}: invalid sample") from exc
            if as_of is not None and timestamp > as_of:
                continue
            groups[row.get("variant") or "all"].append((timestamp, value))

    if not groups and as_of is None:
        raise ValueError(f"{path}: capture contains no samples")

    return [
        summarize_samples(path, metric, service, phase, variant, samples)
        for variant, samples in sorted(groups.items())
    ]


def summarize_samples(
    path: Path,
    metric: str,
    service: str,
    phase: str,
    variant: str,
    samples: list[tuple[datetime, float]],
) -> dict:
    ordered = sorted(samples)
    values = [value for _, value in ordered]
    return {
        "id": f"ev_{service}_{phase}_{variant}",
        "source": path.name,
        "phase": phase,
        "variant": variant,
        "metric": metric,
        "unit": "percent",
        "start": ordered[0][0].isoformat(),
        "end": ordered[-1][0].isoformat(),
        "samples": len(values),
        "mean": round(mean(values), 2),
        "peak": max(values),
    }
