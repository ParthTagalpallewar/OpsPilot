"""Freeze a read-only Prometheus comparison and replay its observations."""

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen

from opspilot.evidence.metrics import summarize_samples
from opspilot.evidence.snapshots import publish_snapshot

MAX_RESPONSE = 2_000_000


def read_matrix(response: dict) -> tuple[dict, list[tuple[datetime, float]]]:
    try:
        data = response["data"]
        if response["status"] != "success" or data["resultType"] != "matrix":
            raise ValueError
        (series,) = data["result"]
        labels = series["metric"]
        if not isinstance(labels, dict):
            raise ValueError
        points = [
            (datetime.fromtimestamp(float(timestamp), UTC), float(value))
            for timestamp, value in series["values"]
        ]
        if not points or any(
            not math.isfinite(value) or value < 0 for _, value in points
        ):
            raise ValueError
    except (KeyError, OSError, OverflowError, TypeError, ValueError) as exc:
        raise ValueError("Expected one nonempty Prometheus percentage series") from exc
    return labels, points


def capture_comparison(
    url: str,
    query: str,
    timestamps: list[str],
    step: int,
    path: Path,
) -> None:
    endpoint = urlsplit(url)
    if (
        endpoint.scheme not in {"http", "https"}
        or not endpoint.hostname
        or endpoint.username is not None
        or endpoint.query
        or endpoint.fragment
    ):
        raise ValueError(
            "Use a Prometheus HTTP(S) base URL without credentials or query"
        )
    bounds = [datetime.fromisoformat(value) for value in timestamps]
    if any(value.utcoffset() is None for value in bounds):
        raise ValueError("All window bounds require UTC offsets")
    first, second, third, fourth = bounds
    if not first < second < third < fourth or step < 1:
        raise ValueError("Specify ordered, disjoint windows and a positive step")
    ranges = [(first, second), (third, fourth)]
    if any((end - start).total_seconds() / step >= 10_000 for start, end in ranges):
        raise ValueError("Each window must use at most 10,000 evaluation points")
    windows = {}
    requested = {}
    for phase, (start, end) in zip(("baseline", "fault"), ranges, strict=True):
        parameters = urlencode(
            {
                "query": query,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "step": step,
                "timeout": "10s",
            }
        )
        with urlopen(
            f"{url.rstrip('/')}/api/v1/query_range?{parameters}", timeout=15
        ) as response:
            body = response.read(MAX_RESPONSE + 1)
        if len(body) > MAX_RESPONSE:
            raise ValueError("Prometheus response exceeded the capture limit")
        windows[phase] = json.loads(body)
        requested[phase] = {"start": start.isoformat(), "end": end.isoformat()}

    payload = {
        "query": query,
        "step_seconds": step,
        "windows": windows,
        "requested_windows": requested,
    }
    compare_windows(payload, path, "capture", "percent")
    publish_snapshot(path, json.dumps(payload).encode())


def compare_windows(
    payload: dict,
    path: Path,
    service: str,
    metric: str,
    *,
    as_of: datetime | None = None,
) -> list[dict]:
    try:
        query = payload["query"]
        step = payload["step_seconds"]
        baseline, fault = (
            read_matrix(payload["windows"][phase]) for phase in ("baseline", "fault")
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"{path}: invalid Prometheus comparison capture") from exc
    if baseline[0] != fault[0]:
        raise ValueError("The Prometheus windows returned different series labels")
    if max(time for time, _ in baseline[1]) >= min(time for time, _ in fault[1]):
        raise ValueError("The Prometheus sample windows overlap")

    evidence = []
    for phase, (labels, points) in zip(
        ("baseline", "fault"), (baseline, fault), strict=True
    ):
        visible = [point for point in points if as_of is None or point[0] <= as_of]
        if not visible:
            continue
        evidence.append(
            {
                **summarize_samples(path, metric, service, phase, "all", visible),
                "query": query,
                "step_seconds": step,
                "series_labels": labels,
            }
        )
    return evidence
