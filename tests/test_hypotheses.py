import shutil
from pathlib import Path

from opspilot.replay import investigate

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


def test_equally_timed_changes_tie_and_review_stays_generic(tmp_path):
    for source in CAPTURES.glob("ad-stats-*.csv"):
        shutil.copy(source, tmp_path)
    original = (CAPTURES / "ad-changes.csv").read_text()
    competing = (
        "deployment,release-v2,active,2026-11-21T14:30:19Z,"
        "2026-11-21T14:31:25Z,fixture.md\n"
    )
    (tmp_path / "ad-changes.csv").write_text(original.rstrip() + "\n" + competing)

    report = investigate("ad-high-cpu", tmp_path)

    assert [candidate["rank"] for candidate in report["hypotheses"]] == [1, 1, 2]
    assert {item["cause"]["name"] for item in report["hypotheses"][:2]} == {
        "adHighCpu",
        "release-v2",
    }
    assert report["hypothesis"]["cause"] is None
