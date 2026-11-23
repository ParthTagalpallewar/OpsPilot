import shutil
from pathlib import Path

from opspilot.replay import investigate

TESTBED = Path(__file__).resolve().parents[2] / "testbed"


def test_unreadable_payment_trace_preserves_warning_and_counts(tmp_path):
    source = TESTBED / "captures" / "checkout-payment"
    shutil.copy(source / "payment-logs.jsonl", tmp_path)
    shutil.copy(source / "payment-requests.json", tmp_path)
    (tmp_path / "payment-traces.json").write_text("{")

    report = investigate("payment-failure", tmp_path)

    assert report["coverage"] == "partial"
    assert report["source_issues"] == [
        {"source": "payment-traces.json", "reason": "invalid"}
    ]
    assert {item["type"] for item in report["evidence"]} == {
        "log_cluster",
        "request_counts",
    }
    assert report["hypothesis"] is None


def test_missing_fault_window_preserves_baseline_without_comparison(tmp_path):
    source = TESTBED / "scenarios" / "ad-stats-baseline.csv"
    shutil.copy(source, tmp_path)

    report = investigate("ad-high-cpu", tmp_path)

    assert report["source_issues"] == [
        {"source": "ad-stats-fault.csv", "reason": "missing"}
    ]
    assert report["hypotheses"] == []
    assert report["observations"] == []
    assert report["evidence"][0]["phase"] == "baseline"
