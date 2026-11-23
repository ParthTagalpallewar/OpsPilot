from pathlib import Path

import pytest

from opspilot.replay import investigate

CAPTURES = Path(__file__).resolve().parents[2] / "testbed" / "captures"


@pytest.mark.parametrize(
    ("capture", "target", "parent"),
    [
        ("payment-controlled", "payment", "payment-capture-client"),
        ("checkout-payment", "checkout", "checkout"),
    ],
)
def test_controlled_payment_capture_links_warnings_and_reports_failure_rates(
    capture, target, parent
):
    report = investigate("payment-failure", CAPTURES / capture)
    evidence = {record["id"]: record for record in report["evidence"]}
    counts = [
        record for record in evidence.values() if record["type"] == "request_counts"
    ]
    assert [
        (row["failed"], row["total"], row["failure_percent"]) for row in counts
    ] == [
        (0, 6, 0.0),
        (6, 6, 100.0),
    ]
    assert {row["target_service"] for row in counts} == {target}
    links = [
        observation
        for observation in report["observations"]
        if {evidence[key]["type"] for key in observation["evidence_ids"]}
        == {"log_cluster", "trace_error"}
    ]
    assert len(links) == 6
    assert all(
        evidence[row["evidence_ids"][1]]["parent_service"] == parent for row in links
    )
