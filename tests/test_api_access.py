import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from opspilot.apps.api.auth import ApiAccess, ClientCredential
from opspilot.apps.api.main import create_app

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


def test_shared_access_roles_and_approval_attribution(tmp_path):
    operator, reviewer, other = "x" * 32, "y" * 32, "z" * 32
    access = ApiAccess(
        [
            ClientCredential(principal="ops", role="operator", token=operator),
            ClientCredential(principal="alex", role="reviewer", token=reviewer),
            ClientCredential(principal="sam", role="reviewer", token=other),
        ]
    )
    app = create_app(tmp_path / "secure.db", CAPTURES, access=access)

    def headers(token):
        return {"Authorization": f"Bearer {token}"}

    async def verify():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            submit = {
                "scenario": "ad-high-cpu",
                "title": "Ad CPU",
                "description": "Replay",
            }
            path = "/v1/incidents"
            assert (await client.post(path, json=submit)).status_code == 401
            assert (
                await client.post(path, json=submit, headers=headers(reviewer))
            ).status_code == 403
            created = await client.post(path, json=submit, headers=headers(operator))
            assert created.status_code == 201
            location = created.headers["Location"]
            assert (await client.get(location + "/events")).status_code == 401
            plan = created.json()["plan"]
            approval = {
                "plan_id": plan["plan_id"],
                "plan_hash": plan["plan_hash"],
                "decision": "approve",
                "reviewer": "spoofed",
            }
            path = location + "/approval"
            blocked = await client.post(path, json=approval, headers=headers(operator))
            assert blocked.status_code == 403
            accepted = await client.post(path, json=approval, headers=headers(reviewer))
            assert accepted.status_code == 200
            result = accepted.json()
            assert result["approval_history"][0]["reviewer"] == "alex"
            preview = result["dry_run_preview"]
            assert preview["plan_hash"] == plan["plan_hash"]
            assert preview["planned_action"] == plan["action"]
            assert preview["executed_actions"] == []
            assert (
                await client.get(location, headers=headers(operator))
            ).json() == result
            retry = await client.post(path, json=approval, headers=headers(reviewer))
            assert retry.json() == accepted.json()
            competing = await client.post(path, json=approval, headers=headers(other))
            assert competing.status_code == 409

    asyncio.run(verify())
