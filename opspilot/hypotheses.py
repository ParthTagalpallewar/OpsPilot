"""Rank resource hypotheses using measured changes and onset timing."""

from collections import defaultdict


def rank_resource_hypotheses(
    windows: list[dict],
    changes: list[dict],
    aligned: list[dict],
    service: str,
    label: str,
) -> list[dict]:
    baseline, *fault = windows
    if not all(record["mean"] > baseline["peak"] for record in fault):
        return []

    onset = fault[0]
    onset_ids = {baseline["id"], onset["id"]}
    aligned_ids = {
        item["evidence_ids"][1]
        for item in aligned
        if onset_ids.issubset(item["evidence_ids"])
    }
    candidates = defaultdict(list)
    for change in changes:
        if change["id"] in aligned_ids:
            candidates[(change["kind"], change["name"])].append(change["id"])

    ranked = [
        {
            "rank": 1,
            "cause": {"kind": kind, "name": name},
            "confidence": "low",
            "statement": (
                f"The timing makes the {name} change a possible contributor "
                f"to elevated {label} on {service}."
            ),
            "evidence_ids": [baseline["id"], *candidate_ids, onset["id"]],
            "recommended_check": (
                "Verify the change timeline and compare request volume, "
                "latency, and traces across the sampled windows."
            ),
        }
        for (kind, name), candidate_ids in sorted(candidates.items())
    ]
    return [
        *ranked,
        {
            "rank": 2 if ranked else 1,
            "cause": None,
            "confidence": "low",
            "statement": (
                f"Elevated {label} on {service} may contribute to the incident."
            ),
            "evidence_ids": [record["id"] for record in windows],
            "recommended_check": (
                "Compare request latency and traces across the sampled windows."
            ),
        },
    ]
