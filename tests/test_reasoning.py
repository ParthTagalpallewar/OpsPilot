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
    response = {
        "stop_reason": "end_turn",
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "statement": "Elevated CPU may contribute to slow requests.",
                        "evidence_ids": evidence_ids,
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
