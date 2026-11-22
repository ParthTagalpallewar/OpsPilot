import asyncio
import json
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from opspilot.apps.api.main import create_app
from opspilot.investigations import InvestigationStore

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


def test_reconnect_replays_pending_events_and_citation_lookup(tmp_path):
    database = tmp_path / "server.db"
    app = create_app(database, CAPTURES)
    store = InvestigationStore(database, CAPTURES)

    async def verify():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            created = await client.post(
                "/v1/incidents",
                json={
                    "scenario": "payment-failure",
                    "title": "Payment warning",
                    "description": "Replay the captured incident.",
                    "queued": True,
                },
            )
            assert created.status_code == 202
            investigation_id = created.json()["investigation_id"]
            (queued,) = store.events_after(investigation_id, 0)
            assert queued["status"] == "queued"
            assert store.process_next()

            location = created.headers["Location"]
            events = await client.get(
                location + "/events", headers={"Last-Event-ID": str(queued["id"])}
            )
            assert events.headers["content-type"].startswith("text/event-stream")
            frames = [
                json.loads(line.removeprefix("data: "))
                for line in events.text.splitlines()
                if line.startswith("data: ")
            ]
            assert [event["status"] for event in frames if "step" not in event] == [
                "running",
                "completed",
            ]
            assert [event["step"] for event in frames if "step" in event] == [
                "collect_payment",
                "report_payment",
                "retrieve_runbook",
                "validate",
            ]
            assert events.text.count("event: step") == 4
            terminal = await client.get(
                location + "/events", headers={"Last-Event-ID": str(frames[-1]["id"])}
            )
            assert terminal.status_code == 204
            document = (await client.get(location)).json()
            expected = document["report"]["evidence"][0]
            evidence = await client.get(location + "/evidence/" + expected["id"])
            assert evidence.json() == expected
            missing = await client.get(location + "/evidence/unknown")
            assert missing.status_code == 404

    asyncio.run(verify())
