import json
import shutil
from datetime import datetime
from pathlib import Path

from opspilot.evidence.rollouts import import_rollouts
from opspilot.replay import investigate

CAPTURES = Path(__file__).resolve().parents[2] / "testbed" / "scenarios"


def test_rollout_correlation_keeps_distinct_sources_and_obeys_cutoff(tmp_path):
    for source in CAPTURES.glob("ad-*.csv"):
        shutil.copy(source, tmp_path)
    event = {
        "kind": "ReplicaSet",
        "metadata": {
            "namespace": "demo",
            "name": "ad-55b7",
            "creationTimestamp": "2026-11-21T14:31:00Z",
            "annotations": {"deployment.kubernetes.io/revision": "3"},
            "ownerReferences": [
                {"kind": "Deployment", "name": "ad", "controller": True}
            ],
        },
    }
    source = tmp_path / "replicasets.json"
    unrelated = {**event, "metadata": {**event["metadata"], "namespace": "elsewhere"}}
    source.write_text(json.dumps({"items": [event, unrelated]}))
    import_rollouts(source, tmp_path, namespace="demo", deployment="ad", service="ad")

    report = investigate("ad-high-cpu", tmp_path)
    evidence = {item["id"]: item for item in report["evidence"]}
    assert evidence["ev_change_ad_2"]["kind"] == "feature_flag"
    event = evidence["ev_rollout_ad_2"]
    assert event["value"] == "revision 3, ReplicaSet ad-55b7 created"
    assert event["origin"] == "replicasets.json#/items/0/metadata"
    assert {
        item["cause"]["kind"] for item in report["hypotheses"] if item["rank"] == 1
    } == {"deployment", "feature_flag"}
    earlier = investigate(
        "ad-high-cpu", tmp_path, as_of=datetime.fromisoformat("2026-11-21T14:30:59Z")
    )
    assert not any(item["id"] == event["id"] for item in earlier["evidence"])
