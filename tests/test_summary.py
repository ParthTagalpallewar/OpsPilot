import asyncio
import re
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from opspilot import cli
from opspilot.apps.api.auth import ApiAccess, ClientCredential
from opspilot.apps.api.main import create_app
from opspilot.replay import investigate
from opspilot.summary import render_markdown

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"
OWN_HEADINGS = {
    "# Incident report: payment-failure (payment)",
    "## Leading hypothesis",
    "## Observations",
    "## Model explanation",
    "## Limitation",
    "## Evidence",
}


def test_summary_lists_hypothesis_guidance_and_every_cited_record():
    report = investigate("ad-high-cpu", CAPTURES)
    summary = render_markdown(report, title="Ad CPU alert")

    assert summary.startswith("# Incident report: ad-high-cpu (ad)\n")
    assert "**Incident:** Ad CPU alert" in summary
    assert report["hypothesis"]["statement"] in summary
    assert "## Runbook guidance" in summary
    for record in report["evidence"]:
        assert f"| `{record['id']}` |" in summary


def test_summary_states_when_no_hypothesis_is_supported():
    summary = render_markdown(investigate("payment-failure", CAPTURES))

    assert (
        "No hypothesis. The evidence does not support attributing a cause." in summary
    )
    assert "## Other hypotheses" not in summary


def test_summary_marks_cutoff_and_partial_coverage():
    cutoff = datetime.fromisoformat("2026-11-21T14:30:19+00:00")
    report = {
        **investigate("ad-high-cpu", CAPTURES, as_of=cutoff),
        "coverage": "partial",
        "source_issues": [{"source": "ad-changes.csv", "reason": "invalid"}],
    }
    summary = render_markdown(report)

    assert "> Evidence visible as of 2026-11-21T14:30:19+00:00." in summary
    assert (
        "> Partial coverage. Unavailable sources: ad-changes.csv (invalid)." in summary
    )


def test_summary_escapes_markup_from_telemetry_and_model_text():
    hostile = "# Heading\n[click](http://evil.example) <img src=x> | cell"
    report = {
        "scenario": "payment-failure",
        "service": "payment",
        "hypothesis": None,
        "hypotheses": [],
        "observations": [{"statement": hostile, "evidence_ids": ["ev_a"]}],
        "limitation": "1. not a list",
        "model_explanation": {
            "status": "generated",
            "statement": hostile,
            "evidence_ids": ["ev_a"],
            "model": "test-model",
        },
        "evidence": [{"id": "ev_a", "type": "log_cluster", "source": "logs.jsonl"}],
    }
    summary = render_markdown(report, title=hostile)

    assert "\\[click\\](http://evil.example)" in summary
    assert re.search(r"(?<!\\)[<\[|]", summary.split("## Evidence")[0]) is None
    assert "1\\. not a list" in summary
    headings = {line for line in summary.splitlines() if line.startswith("#")}
    assert headings == OWN_HEADINGS


def test_replay_command_prints_markdown(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["opspilot", "replay", "ad-high-cpu", "--captures", str(CAPTURES)]
        + ["--format", "markdown"],
    )
    cli.main()

    assert capsys.readouterr().out == render_markdown(
        investigate("ad-high-cpu", CAPTURES)
    )


def test_summary_endpoint_serves_completed_reports_only(tmp_path):
    app = create_app(tmp_path / "summary.db", CAPTURES)
    incident = {"scenario": "ad-high-cpu", "title": "Ad CPU [page]", "description": "x"}

    async def verify():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            created = await client.post("/v1/incidents", json=incident)
            summary = await client.get(created.headers["Location"] + "/summary")
            assert summary.status_code == 200
            assert summary.headers["content-type"] == "text/markdown; charset=utf-8"
            assert summary.text == render_markdown(
                created.json()["report"], title="Ad CPU [page]"
            )

            queued = await client.post(
                "/v1/incidents", json={**incident, "queued": True}
            )
            pending = await client.get(queued.headers["Location"] + "/summary")
            assert pending.status_code == 409
            assert pending.json()["detail"].endswith("investigation is queued")
            missing = await client.get(f"/v1/investigations/{uuid4()}/summary")
            assert missing.status_code == 404

    asyncio.run(verify())


def test_summary_endpoint_requires_a_reader_credential(tmp_path):
    operator, webhook = "o" * 32, "w" * 32
    access = ApiAccess(
        [
            ClientCredential(principal="ops", role="operator", token=operator),
            ClientCredential(principal="alerts", role="webhook", token=webhook),
        ]
    )
    app = create_app(tmp_path / "secure.db", CAPTURES, access=access)

    async def verify():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            created = await client.post(
                "/v1/incidents",
                json={"scenario": "ad-high-cpu", "title": "Ad CPU", "description": "x"},
                headers={"Authorization": f"Bearer {operator}"},
            )
            path = created.headers["Location"] + "/summary"
            assert (await client.get(path)).status_code == 401
            denied = await client.get(
                path, headers={"Authorization": f"Bearer {webhook}"}
            )
            assert denied.status_code == 403
            allowed = await client.get(
                path, headers={"Authorization": f"Bearer {operator}"}
            )
            assert allowed.status_code == 200

    asyncio.run(verify())
