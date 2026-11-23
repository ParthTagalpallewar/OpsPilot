"""Select the reviewed fields permitted in the outbound model context."""

from hashlib import sha256

REVIEWED_RUNBOOKS = {
    # The exact heading and excerpt must match a reviewed demo runbook revision.
    "e5c9bd6be0c1d4a51305ae5540407f0dbebc02247ece5a9499695f099d34eae6",
    "5f709c0d8d539f4aaa2285ae05bd2cc826271e2e1f471d992cfc20be8dce83d1",
    "81d404e7e06fd11a8364329aaed473e5be6a75c7d355bf7fc7a3e2c3511d6999",
    "2bf87dc6f7237e6f93b61a8c43a22dbbed0fa676ef67f57f14fed33fc34db8c0",
}


def select_evidence(record: dict) -> dict | None:
    if record.get("metric") in {"cpu_percent", "mem_percent"}:
        return {
            key: record[key] for key in ("metric", "phase", "samples", "mean", "peak")
        }
    if record.get("type") == "change_event":
        if record.get("kind") in {"feature_flag", "deployment"}:
            return {
                "type": record["kind"],
                "earliest": record["earliest"],
                "latest": record["latest"],
            }
    if record.get("type") == "runbook":
        body = f"{record['heading']}\n{record['excerpt']}"
        if sha256(body.encode()).hexdigest() in REVIEWED_RUNBOOKS:
            return {"type": "runbook", "text": body}
    return None


def model_context(report: dict) -> tuple[dict, dict[str, str], set[str]]:
    evidence = []
    originals = {}
    metrics = set()
    for record in report["evidence"]:
        selected = select_evidence(record)
        if selected is None:
            continue
        alias = f"e{len(evidence) + 1}"
        originals[alias] = record["id"]
        evidence.append({"id": alias, **selected})
        if "metric" in selected:
            metrics.add(alias)

    supporting = set(report["hypothesis"]["evidence_ids"])
    return (
        {
            "service": report["service"],
            "supporting_evidence_ids": [
                alias for alias, original in originals.items() if original in supporting
            ],
            "evidence": evidence,
        },
        originals,
        metrics,
    )
