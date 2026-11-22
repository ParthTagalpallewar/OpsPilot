import json

import pytest

from opspilot.evidence.otlp_logs import import_payment_logs
from opspilot.replay import investigate


def test_otlp_import_preserves_selected_warning_context(tmp_path):
    source = tmp_path / "export.json"
    output = tmp_path / "capture"
    warning = {
        "observedTimeUnixNano": "1795305600123456789",
        "severityNumber": 13,
        "body": {"stringValue": "Payment request failed"},
        "traceId": "AB" * 16,
        "spanId": "CD" * 8,
        "attributes": [{"key": "irrelevant", "value": {"stringValue": "omit me"}}],
    }

    def resource(service):
        return {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": service}}
                ]
            },
            "scopeLogs": [{"logRecords": [warning, {**warning, "severityNumber": 9}]}],
        }

    source.write_text(
        json.dumps({"resourceLogs": [resource("checkout"), resource("payment")]})
    )

    path = import_payment_logs(source, output)
    with pytest.raises(FileExistsError):
        import_payment_logs(source, output)
    (record,) = investigate("payment-failure", output)["evidence"]

    assert "omit me" not in path.read_text()
    assert record["severity"] == "warn"
    assert record["count"] == 1
    assert record["records"] == [
        {
            "line": 1,
            "timestamp": "2026-11-22T00:00:00.123456+00:00",
            "origin": "export.json#/resourceLogs/1/scopeLogs/0/logRecords/0",
            "trace_id": "ab" * 16,
            "span_id": "cd" * 8,
        }
    ]
