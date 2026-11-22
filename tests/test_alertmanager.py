import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from opspilot.apps.api.main import create_app
from opspilot.investigations import InvestigationStore

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


def test_alert_delivery_retries_reuse_the_same_job(tmp_path):
    database = tmp_path / "alerts.db"
    app = create_app(database, CAPTURES)
    endpoint = "/v1/webhooks/alertmanager"
    alert = {
        "status": "firing",
        "fingerprint": "04af",
        "startsAt": "2026-11-22T00:00:00Z",
        "labels": {"alertname": "HighAdCpu", "opspilot_scenario": "ad-high-cpu"},
    }

    async def verify():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            first, retry = await asyncio.gather(
                client.post(endpoint, json={"alerts": [alert]}),
                client.post(
                    endpoint,
                    json={
                        "alerts": [{**alert, "startsAt": "2026-11-22T05:30:00+05:30"}]
                    },
                ),
            )
            assert first.status_code == retry.status_code == 202
            assert first.json() == retry.json()
            store = InvestigationStore(database, CAPTURES)
            assert store.process_next()
            assert not store.process_next()
            ignored = await client.post(
                endpoint,
                json={
                    "alerts": [
                        {**alert, "status": "resolved"},
                        {**alert, "labels": {"opspilot_scenario": "unknown"}},
                    ]
                },
            )
            assert ignored.json() == {"investigations": [], "ignored_alerts": 2}
            recurrence = await client.post(
                endpoint,
                json={"alerts": [{**alert, "startsAt": "2026-11-22T00:10:00Z"}]},
            )
            assert recurrence.json()["investigations"] != first.json()["investigations"]
            assert store.process_next()
            assert not store.process_next()

    asyncio.run(verify())
