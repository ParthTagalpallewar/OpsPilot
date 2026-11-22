import json

import pytest

from opspilot.evidence.logs import summarize_logs


def test_collects_warning_aliases_and_preserves_source_lines(tmp_path):
    path = tmp_path / "capture.jsonl"
    event = {
        "service": "payment",
        "severity": "WARN",
        "timestamp": "2026-11-21T19:33:33",
        "message": "Payment request failed. Invalid token.",
        "origin": "scenario.md",
    }
    rows = [
        event,
        {**event, "service": "checkout"},
        {**event, "severity": "info"},
        {**event, "severity": "warning"},
    ]
    path.write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")

    (cluster,) = summarize_logs(path, "payment")

    assert cluster["severity"] == "warn"
    assert cluster["count"] == 2
    assert [row["line"] for row in cluster["records"]] == [1, 4]
    assert summarize_logs(path, "payment") == [cluster]


def test_invalid_log_record_reports_its_location(tmp_path):
    path = tmp_path / "capture.jsonl"
    path.write_text("\n[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"capture\.jsonl:2: invalid log record"):
        summarize_logs(path, "payment")
