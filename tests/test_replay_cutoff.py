from datetime import UTC, datetime
from pathlib import Path

from opspilot.investigations import InvestigationStore
from opspilot.replay import investigate

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


def test_cutoff_limits_queued_report_to_visible_records(tmp_path):
    cutoff = datetime(2026, 11, 21, 14, 31, 25, tzinfo=UTC)
    store = InvestigationStore(tmp_path / "replay.db", CAPTURES)
    job = store.create(
        "ad-high-cpu", "Ad CPU", "Replay onset", queued=True, as_of=cutoff
    )
    assert store.process_next()
    report = store.get(job["investigation_id"])["report"]
    assert report["as_of"] == cutoff.isoformat()
    (fault,) = [item for item in report["evidence"] if item.get("phase") == "fault"]
    assert fault["samples"] == 1
    assert fault["end"] == cutoff.isoformat()
    assert report["guidance"] == []


def test_early_replay_abstains_without_an_incident_window():
    cutoff = datetime(2026, 11, 21, 14, 30, 19, tzinfo=UTC)
    report = investigate("ad-high-cpu", CAPTURES, as_of=cutoff)

    assert report["hypothesis"] is None
    (baseline,) = report["evidence"]
    assert baseline["phase"] == "baseline"

    payment = investigate("payment-failure", CAPTURES, as_of=cutoff)
    assert payment["evidence"] == []
