from pathlib import Path
from unittest.mock import patch

from opspilot.evidence.runbooks import retrieve_runbooks

RUNBOOKS = Path(__file__).resolve().parents[2] / "testbed" / "runbooks"


def test_semantic_results_can_supply_guidance_when_keywords_miss(monkeypatch):
    query = "authorization refused"
    monkeypatch.delenv("OPSPILOT_RUNBOOK_SEARCH", raising=False)
    assert retrieve_runbooks(RUNBOOKS, "payment", query) == []

    monkeypatch.setenv("OPSPILOT_RUNBOOK_SEARCH", "hybrid")
    with patch(
        "opspilot.evidence.runbooks.semantic_order", return_value=[0, 1]
    ) as rank:
        (record,) = retrieve_runbooks(RUNBOOKS, "payment", query)

    assert record["heading"] == "Investigate Payment failures"
    assert record["retrieval"]["keyword_rank"] is None
    assert record["retrieval"]["semantic_rank"] == 1
    assert len(rank.call_args.args[1]) == 2


def test_rank_fusion_prefers_agreement(tmp_path, monkeypatch):
    (tmp_path / "payment.md").write_text(
        "# Payment\n## Payment charge\nCharge.\n"
        "## Payment charge review\nReview the issue.\n"
        "## Payment verification\nVerify the issue.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPSPILOT_RUNBOOK_SEARCH", "hybrid")
    with (
        patch("opspilot.evidence.runbooks.keyword_order", return_value=[0, 1]),
        patch("opspilot.evidence.runbooks.semantic_order", return_value=[2, 1]),
    ):
        (record,) = retrieve_runbooks(tmp_path, "payment", "charge")
    assert record["heading"] == "Payment charge review"
    assert record["retrieval"]["keyword_rank"] == 2
    assert record["retrieval"]["semantic_rank"] == 2


def test_vector_failure_preserves_report_and_keyword_guidance(monkeypatch):
    from opspilot.replay import investigate

    monkeypatch.setenv("OPSPILOT_RUNBOOK_SEARCH", "hybrid")
    monkeypatch.setenv("OPSPILOT_VECTOR_DSN", "postgresql://unused")
    with patch("opspilot.evidence.runbooks.pgvector_order", side_effect=ValueError):
        captures = RUNBOOKS.parent / "scenarios"
        report = investigate("ad-high-cpu", captures)

    assert report["coverage"] == "partial"
    assert report["source_issues"] == [
        {"source": "runbook_semantic", "reason": "unavailable"}
    ]
    assert report["hypothesis"]["cause"]["name"] == "adHighCpu"
    (runbook,) = [item for item in report["evidence"] if item.get("type") == "runbook"]
    assert runbook["heading"] == "Investigate sustained Ad CPU"
    assert runbook["retrieval"]["mode"] == "keyword_fallback"
    assert report["guidance"][0]["evidence_ids"] == [runbook["id"]]
