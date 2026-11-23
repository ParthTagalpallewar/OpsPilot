import asyncio
import io
import json
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

from httpx import ASGITransport, AsyncClient

from opspilot.apps.api.main import create_app
from opspilot.investigations import InvestigationStore
from opspilot.live_metrics import LiveMetrics


def test_live_alert_queues_for_worker_and_deduplicates(tmp_path, monkeypatch):
    db = tmp_path / "alert.db"
    captures = tmp_path / "historical"
    app = create_app(db, captures, live_scenarios=frozenset({"ad-high-cpu"}))
    live = LiveMetrics("http://127.0.0.1:9090", {"ad-high-cpu": "metric"}, tmp_path)
    store = InvestigationStore(db, captures, live_metrics=live)

    async def verify():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            alert = {
                "status": "firing",
                "fingerprint": "dd",
                "startsAt": "2026-11-23T02:30:00Z",
                "labels": {"opspilot_mode": "live", "opspilot_scenario": "ad-high-cpu"},
            }
            endpoint = "/v1/webhooks/alertmanager"
            created = await client.post(endpoint, json={"alerts": [alert]})
            retry = await client.post(endpoint, json={"alerts": [alert]})
            assert created.status_code == retry.status_code == 202
            assert created.json() == retry.json()
            result = created.json()["investigations"][0]
            assert result["status"] == "queued"
            assert list(tmp_path.glob("*/ad-prometheus.json")) == []
            unsupported = {
                "alerts": [
                    {
                        **alert,
                        "labels": {
                            **alert["labels"],
                            "opspilot_scenario": "payment-failure",
                        },
                    }
                ]
            }
            ignored = await client.post(endpoint, json=unsupported)
            assert ignored.json()["ignored_alerts"] == 1
            return result["investigation_id"]

    investigation_id = asyncio.run(verify())
    document = store.get(investigation_id)
    assert document["capture_mode"] == "live_metrics"
    assert document["live_alert_at"] == "2026-11-23T02:30:00+00:00"

    requests = []

    def fetch(url, *, timeout):
        query = parse_qs(urlsplit(url).query)
        requests.append(query)
        timestamp = datetime.fromisoformat(query["start"][0]).timestamp()
        value = "2" if len(requests) == 1 else "90"
        return io.BytesIO(
            json.dumps(
                {
                    "status": "success",
                    "data": {
                        "resultType": "matrix",
                        "result": [{"metric": {}, "values": [[timestamp, value]]}],
                    },
                }
            ).encode()
        )

    monkeypatch.setattr("opspilot.evidence.prometheus.urlopen", fetch)
    assert store.process_next()
    document = store.get(investigation_id)
    assert document["status"] == "completed"
    assert [record["mean"] for record in document["report"]["evidence"]] == [2, 90]
    assert requests[1]["end"] == ["2026-11-23T02:30:00+00:00"]
    assert (tmp_path / investigation_id / "ad-prometheus.json").is_file()
    assert not store.process_next()


def test_payment_alert_discovers_a_failed_trace(tmp_path, monkeypatch):
    from pathlib import Path

    from opspilot.live_traces import LivePaymentTraces

    fixture = Path(__file__).resolve().parents[1] / "testbed/captures/checkout-payment"
    export = json.loads((fixture / "payment-traces.json").read_bytes())
    resources_by_trace = {}
    for resource in export["resourceSpans"]:
        for scope in resource["scopeSpans"]:
            for span in scope["spans"]:
                resources_by_trace.setdefault(span["traceId"], []).append(
                    {
                        **resource,
                        "scopeSpans": [{**scope, "spans": [span]}],
                    }
                )

    requested = []
    expected = min(resources_by_trace)

    def fetch(url, *, timeout):
        endpoint = urlsplit(url)
        requested.append(endpoint.path)
        if endpoint.path.endswith("/traces"):
            assert parse_qs(endpoint.query) == {
                "query.serviceName": ["payment"],
                "query.startTimeMin": ["2026-11-23T02:10:00+00:00"],
                "query.startTimeMax": ["2026-11-23T02:20:00+00:00"],
                "query.searchDepth": ["20"],
            }
            return io.BytesIO(
                b"\n".join(
                    json.dumps({"result": {"resourceSpans": resources}}).encode()
                    for _, resources in sorted(resources_by_trace.items(), reverse=True)
                )
            )
        assert endpoint.path.endswith(f"/traces/{expected}")
        return io.BytesIO(
            json.dumps(
                {"result": {"resourceSpans": resources_by_trace[expected]}}
            ).encode()
        )

    monkeypatch.setattr("opspilot.evidence.traces.urlopen", fetch)
    db = tmp_path / "alert.db"
    app = create_app(db, tmp_path, live_scenarios=frozenset({"payment-failure"}))
    collector = LivePaymentTraces(
        "http://jaeger/jaeger/ui", tmp_path, fixture / "otel-payment-logs.json"
    )
    store = InvestigationStore(db, tmp_path, live_traces=collector)

    async def submit():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            result = await client.post(
                "/v1/webhooks/alertmanager",
                json={
                    "alerts": [
                        {
                            "status": "firing",
                            "fingerprint": "ee",
                            "startsAt": "2026-11-23T02:20:00Z",
                            "labels": {
                                "opspilot_mode": "live",
                                "opspilot_scenario": "payment-failure",
                            },
                        }
                    ]
                },
            )
            assert result.status_code == 202
            return result.json()["investigations"][0]["investigation_id"]

    investigation_id = asyncio.run(submit())
    assert not requested
    assert store.process_next()
    document = store.get(investigation_id)
    assert document["status"] == "completed"
    report = document["report"]
    assert {item["type"] for item in report["evidence"]} == {
        "log_cluster",
        "trace_error",
    }
    assert any(len(row["evidence_ids"]) == 2 for row in report["observations"])
    assert requested == [
        "/jaeger/ui/api/v3/traces",
        f"/jaeger/ui/api/v3/traces/{expected}",
    ]
