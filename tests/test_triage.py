import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from opspilot.apps.api.main import create_app
from opspilot.investigations import InvestigationStore

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


def test_free_text_routes_only_supported_incidents(tmp_path):
    database = tmp_path / "triage.db"
    app = create_app(database, CAPTURES)
    path = "/v1/incidents"

    async def verify():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            unknown = await client.post(
                path,
                json={
                    "title": "Slow app",
                    "description": "Some requests are slow",
                    "queued": True,
                },
            )
            assert unknown.status_code == 422
            mixed = {
                "title": "Ad CPU and Email memory",
                "description": "Both increased",
            }
            ambiguous = await client.post(path, json=mixed)
            assert ambiguous.status_code == 422
            store = InvestigationStore(database, CAPTURES)
            assert not store.process_next()

            routed = await client.post(
                path,
                json={
                    "title": "Payment API returning 500",
                    "description": "Checkout fails",
                    "queued": True,
                },
            )
            assert routed.status_code == 202
            assert store.process_next()
            result = await client.get(routed.headers["Location"])
            assert result.json()["report"]["scenario"] == "payment-failure"

            with_hint = await client.post(path, json={**mixed, "service": "email"})
            assert with_hint.status_code == 201
            assert with_hint.json()["report"]["scenario"] == "email-memory-leak"

    asyncio.run(verify())
