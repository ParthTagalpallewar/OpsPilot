import io
import json
from pathlib import Path
from unittest.mock import patch

from opspilot.replay import investigate

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


def test_claude_explanation_accepts_citations_and_keeps_baseline(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPSPILOT_CLAUDE_MODEL", "test-model")
    baseline = investigate("ad-high-cpu", CAPTURES)
    evidence_ids = baseline["hypothesis"]["evidence_ids"]
    ordered = baseline["evidence"]
    aliases = [
        f"e{index + 1}"
        for evidence_id in evidence_ids
        for index, record in enumerate(ordered)
        if record["id"] == evidence_id
    ]
    response = {
        "stop_reason": "end_turn",
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "statement": "Elevated CPU may contribute to slow requests.",
                        "evidence_ids": aliases,
                    }
                ),
            }
        ],
    }
    with patch(
        "opspilot.reasoning.urlopen",
        return_value=io.BytesIO(json.dumps(response).encode()),
    ) as provider:
        result = investigate("ad-high-cpu", CAPTURES, with_claude=True)

    explanation = result.pop("model_explanation")
    assert explanation["status"] == "generated"
    assert explanation["evidence_ids"] == evidence_ids
    assert result == baseline
    assert provider.call_count == 1


def test_invalid_model_citation_is_discarded(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPSPILOT_CLAUDE_MODEL", "test-model")
    response = {
        "stop_reason": "end_turn",
        "content": [
            {
                "type": "text",
                "text": '{"statement":"Unsupported claim","evidence_ids":["unknown"]}',
            }
        ],
    }
    with patch(
        "opspilot.reasoning.urlopen",
        return_value=io.BytesIO(json.dumps(response).encode()),
    ):
        result = investigate("ad-high-cpu", CAPTURES, with_claude=True)

    assert result["model_explanation"] == {"status": "invalid_citations"}
    assert result["hypothesis"] is not None


def test_payment_abstains_before_contacting_provider():
    with patch("opspilot.reasoning.urlopen") as provider:
        report = investigate("payment-failure", CAPTURES, with_claude=True)
    assert report["model_explanation"] == {"status": "insufficient_evidence"}
    provider.assert_not_called()


def test_outbound_context_excludes_unreviewed_text(monkeypatch):
    from opspilot.reasoning import explain_report

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPSPILOT_CLAUDE_MODEL", "test-model")
    report = investigate("ad-high-cpu", CAPTURES)
    report["evidence"] += [
        {
            "type": "runbook",
            "id": "runbook-secret-marker",
            "heading": "Hidden",
            "excerpt": "private-token-marker",
        }
    ]
    report["hypothesis"]["statement"] = "private-incident-marker"
    for item in report["evidence"]:
        item["source"] = "private-path-marker"

    with patch("opspilot.reasoning.urlopen", side_effect=ValueError) as provider:
        assert explain_report(report) == {"status": "provider_unavailable"}
    request = provider.call_args.args[0]
    context = json.loads(json.loads(request.data)["messages"][0]["content"])
    assert "private-" not in request.data.decode()
    assert "runbook-secret-marker" not in request.data.decode()
    assert "Investigate sustained Ad CPU" in request.data.decode()
    assert set(context) == {"service", "supporting_evidence_ids", "evidence"}


def test_provider_retry_is_bounded_and_skips_permanent_errors():
    from urllib.error import HTTPError
    from urllib.request import Request

    from opspilot.reasoning import fetch_response

    request = Request("https://example.invalid")
    for status, attempts in [(503, 2), (401, 1)]:
        errors = [
            HTTPError(request.full_url, status, "error", {}, io.BytesIO())
            for _ in range(attempts)
        ]
        with (
            patch("opspilot.reasoning.urlopen", side_effect=errors) as provider,
            patch("opspilot.reasoning.sleep") as wait,
        ):
            assert fetch_response(request) is None
        assert provider.call_count == attempts
        assert wait.call_count == attempts - 1
