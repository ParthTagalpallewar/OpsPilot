import json
import shutil
from pathlib import Path

from opspilot.live_traces import LivePaymentTraces
from opspilot.replay import investigate

FIXTURE = Path(__file__).resolve().parents[2] / "testbed/captures/checkout-payment"


def test_live_trace_freezes_only_matching_collector_logs(tmp_path):
    captures = tmp_path / "investigation"
    captures.mkdir()
    shutil.copy(FIXTURE / "payment-traces.json", captures)
    source = tmp_path / "collector.jsonl"
    logs = json.loads((FIXTURE / "otel-payment-logs.json").read_text())
    trace = logs["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]["traceId"]
    source.write_text(json.dumps({"resourceLogs": []}) + "\n" + json.dumps(logs) + "\n")
    collector = LivePaymentTraces("http://unused", tmp_path, source)

    collector.collect("investigation", trace)
    report = investigate("payment-failure", captures)
    (cluster,) = [item for item in report["evidence"] if item["type"] == "log_cluster"]
    assert cluster["count"] == 1
    assert cluster["records"][0]["origin"].startswith("collector.jsonl:2#")
    assert any(
        cluster["id"] in row["evidence_ids"] and len(row["evidence_ids"]) == 2
        for row in report["observations"]
    )

    source.unlink()
    assert collector.collect("investigation", trace) == captures
    assert investigate("payment-failure", captures) == report


def test_missing_collector_export_keeps_trace_evidence(tmp_path):
    captures = tmp_path / "investigation"
    captures.mkdir()
    shutil.copy(FIXTURE / "payment-traces.json", captures)
    collector = LivePaymentTraces("http://unused", tmp_path, tmp_path / "missing.jsonl")
    collector.collect("investigation", "a" * 32)

    report = investigate("payment-failure", captures)
    assert report["coverage"] == "partial"
    assert report["source_issues"] == [
        {"source": "payment_log_export", "reason": "missing"}
    ]
    assert {item["type"] for item in report["evidence"]} == {"trace_error"}


def test_live_payment_rates_are_cited_as_sampled_means(tmp_path, monkeypatch):
    from datetime import datetime

    captures = tmp_path / "investigation"
    captures.mkdir()
    shutil.copy(FIXTURE / "payment-traces.json", captures)

    def comparison(url, query, alert_time, path):
        response = {
            phase: {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [{"metric": {}, "values": [[timestamp, value]]}],
                },
            }
            for phase, timestamp, value in [
                ("baseline", 1795305600, "2"),
                ("fault", 1795306200, "80"),
            ]
        }
        path.write_text(
            json.dumps({"windows": response, "query": query, "step_seconds": 30})
        )

    monkeypatch.setattr("opspilot.live_traces.capture_alert_comparison", comparison)
    collector = LivePaymentTraces(
        "http://unused", tmp_path, failure_rate=("http://metrics", "q")
    )
    collector.collect(
        "investigation", "a" * 32, datetime.fromisoformat("2026-11-23T02:30:00Z")
    )

    report = investigate("payment-failure", captures)
    rates = [
        item
        for item in report["evidence"]
        if item.get("metric") == "payment_failure_percent"
    ]
    assert [item["mean"] for item in rates] == [2, 80]
    assert all(
        "mean sampled Payment failure rate" in item["statement"]
        for item in report["observations"][-2:]
    )
    assert report["hypothesis"] is None
