"""Collect Jaeger evidence for a queued Payment alert."""

import json
import os
from datetime import datetime
from pathlib import Path

from opspilot.evidence.otlp_logs import NoMatchingPaymentLogs, import_payment_logs
from opspilot.evidence.snapshots import publish_snapshot
from opspilot.evidence.traces import (
    capture_payment_trace,
    discover_payment_trace,
    read_failed_spans,
)
from opspilot.live_metrics import capture_alert_comparison


class LivePaymentTraces:
    def __init__(
        self,
        url: str,
        root: Path,
        log_export: Path | None = None,
        *,
        failure_rate: tuple[str, str] | None = None,
    ):
        self.url = url
        self.root = root
        self.log_export = log_export
        self.failure_rate = failure_rate

    def collect(
        self,
        investigation_id: str,
        trace_id: str | None,
        alert_time: datetime | None = None,
    ) -> Path:
        captures = self.root / investigation_id
        path = captures / "payment-traces.json"
        status = captures / "payment-trace-collection.json"
        if not path.is_file() and not status.is_file():
            try:
                if trace_id is None and alert_time is not None:
                    trace_id = discover_payment_trace(self.url, alert_time, path)
                if trace_id is None:
                    self.record_issue(status, "no_match")
                else:
                    capture_payment_trace(self.url, trace_id, captures)
            except FileExistsError:
                # Use the snapshot created by the competing attempt.
                pass
            except (OSError, ValueError):
                self.record_issue(status, "unavailable")
        if self.log_export is not None and path.is_file():
            spans = read_failed_spans(path, "payment")
            if spans:
                self.collect_logs(self.log_export, captures, spans[0]["trace_id"])
        if self.failure_rate is not None and alert_time is not None:
            path = captures / "payment-prometheus.json"
            status = captures / "payment-metrics-collection.json"
            if not path.is_file() and not status.is_file():
                try:
                    capture_alert_comparison(*self.failure_rate, alert_time, path)
                except FileExistsError:
                    pass
                except (OSError, ValueError):
                    self.record_issue(status, "unavailable")
        return captures

    @staticmethod
    def record_issue(status: Path, reason: str) -> None:
        try:
            publish_snapshot(status, json.dumps({"reason": reason}).encode())
        except FileExistsError:
            pass

    def collect_logs(self, source: Path, captures: Path, trace_id: str) -> None:
        status = captures / "payment-log-collection.json"
        if status.is_file() or (captures / "payment-logs.jsonl").is_file():
            return
        try:
            import_payment_logs(source, captures, trace_id=trace_id)
            return
        except FileExistsError:
            return
        except FileNotFoundError:
            reason = "missing"
        except OSError:
            reason = "unreadable"
        except NoMatchingPaymentLogs:
            reason = "no_match"
        except ValueError:
            reason = "invalid"
        self.record_issue(status, reason)


def configured_live_traces() -> LivePaymentTraces | None:
    url = os.environ.get("OPSPILOT_JAEGER_URL", "").strip()
    if not url:
        return None
    logs = os.environ.get("OPSPILOT_PAYMENT_LOG_EXPORT")
    prometheus = os.environ.get("OPSPILOT_PROMETHEUS_URL", "").strip()
    query = os.environ.get("OPSPILOT_PROMQL_PAYMENT_FAILURE_RATE", "").strip()
    return LivePaymentTraces(
        url,
        Path(os.environ.get("OPSPILOT_LIVE_CAPTURES", "live-captures")),
        Path(logs) if logs else None,
        failure_rate=(prometheus, query) if prometheus and query else None,
    )
