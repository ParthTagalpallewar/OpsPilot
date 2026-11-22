import io
import json
from unittest.mock import patch

from opspilot.evidence.traces import capture_payment_trace
from opspilot.replay import investigate


def test_replay_cites_payment_error_and_direct_parent(tmp_path):
    checkout = {
        "traceId": "a" * 32,
        "spanId": "b" * 16,
        "name": "PlaceOrder",
        "startTimeUnixNano": "1000000000",
        "endTimeUnixNano": "1050000000",
    }
    payment = {
        **checkout,
        "spanId": "c" * 16,
        "parentSpanId": checkout["spanId"],
        "name": "Charge",
        "endTimeUnixNano": "1020000000",
        "status": {"code": 2},
    }
    data = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service}}
                    ]
                },
                "scopeSpans": [{"spans": [span]}],
            }
            for service, span in [("checkout", checkout), ("payment", payment)]
        ]
    }
    with patch(
        "opspilot.evidence.traces.urlopen",
        return_value=io.BytesIO(json.dumps({"result": data}).encode()),
    ) as network:
        path = capture_payment_trace("http://localhost:16686", "a" * 32, tmp_path)
    assert path.name == "payment-traces.json"
    assert network.call_args.args[0].endswith("/api/v3/traces/" + "a" * 32)

    report = investigate("payment-failure", tmp_path)

    trace = next(item for item in report["evidence"] if item["type"] == "trace_error")
    assert trace["duration_ms"] == 20
    assert trace["parent_service"] == "checkout"
    assert report["hypothesis"] is None
    assert report["observations"][-1]["evidence_ids"] == [trace["id"]]

    log = {
        "service": "payment",
        "severity": "warn",
        "timestamp": "2026-11-21T19:33:33Z",
        "message": "Charge failed",
        "origin": "test",
        "trace_id": payment["traceId"].upper(),
        "span_id": payment["spanId"],
    }
    (tmp_path / "payment-logs.jsonl").write_text(
        "\n".join(map(json.dumps, [log, {**log, "span_id": checkout["spanId"]}])),
        encoding="utf-8",
    )
    linked = investigate("payment-failure", tmp_path)
    cluster = next(item for item in linked["evidence"] if item["type"] == "log_cluster")
    match = linked["observations"][-1]
    assert match["evidence_ids"] == [cluster["id"], trace["id"]]
    assert "log lines 1 share" in match["statement"]
