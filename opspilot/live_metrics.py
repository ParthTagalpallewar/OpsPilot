"""Collect a fresh resource snapshot on behalf of a queued alert."""

import os
from datetime import datetime, timedelta
from pathlib import Path

from opspilot.evidence.prometheus import capture_comparison
from opspilot.replay import METRIC_SCENARIOS


def capture_alert_comparison(url: str, query: str, alert_time: datetime, path: Path):
    windows = [alert_time - timedelta(minutes=offset) for offset in (25, 15, 10, 0)]
    capture_comparison(url, query, [stamp.isoformat() for stamp in windows], 30, path)


class LiveMetrics:
    def __init__(self, url: str, queries: dict[str, str], root: Path):
        self.url = url
        self.queries = queries
        self.root = root

    def collect(
        self, investigation_id: str, scenario: str, alert_time: datetime
    ) -> Path:
        query = self.queries.get(scenario)
        if not query:
            raise ValueError("Live metrics are unavailable for this scenario")
        service, _, _ = METRIC_SCENARIOS[scenario]
        captures = self.root / investigation_id
        path = captures / f"{service}-prometheus.json"
        if not path.is_file():
            try:
                capture_alert_comparison(self.url, query, alert_time, path)
            except FileExistsError:
                # Another attempt may have published the same job's snapshot.
                pass
        return captures


def configured_live_metrics() -> LiveMetrics | None:
    url = os.environ.get("OPSPILOT_PROMETHEUS_URL", "").strip()
    queries = {
        scenario: query
        for scenario, (service, _, _) in METRIC_SCENARIOS.items()
        if (query := os.environ.get(f"OPSPILOT_PROMQL_{service.upper()}", "").strip())
    }
    if not url or not queries:
        return None
    return LiveMetrics(
        url, queries, Path(os.environ.get("OPSPILOT_LIVE_CAPTURES", "live-captures"))
    )
