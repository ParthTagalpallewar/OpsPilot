"""Score frozen replay reports against independent expectations."""

import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from opspilot.replay import SCENARIOS, investigate
from opspilot.telemetry import tracer


def score_report(report: dict, expected: dict) -> dict:
    counts = Counter(record["id"] for record in report["evidence"])
    claims = [*report["observations"], *report.get("guidance", [])]
    hypothesis = report["hypothesis"]
    candidates = report.get("hypotheses")
    claims.extend(
        candidates if candidates is not None else [hypothesis] if hypothesis else []
    )
    leaders = [item["cause"] for item in (candidates or []) if item["rank"] == 1]
    expected_cause = expected.get("expected_leading_cause")

    cited_ids = set()
    resolved_claims = 0
    for claim in claims:
        ids = claim["evidence_ids"]
        if ids and all(counts[evidence_id] == 1 for evidence_id in ids):
            resolved_claims += 1
            cited_ids.update(ids)

    missing = [
        target
        for target in expected["expected_records"]
        if not any(
            record["id"] in cited_ids
            and all(record.get(key) == value for key, value in target.items())
            for record in report["evidence"]
        )
    ]
    checks = {
        "service": report["service"] == expected["service"],
        "citation_resolution": bool(claims) and resolved_claims == len(claims),
        "expected_evidence_cited": not missing,
        "hypothesis_presence": (
            (hypothesis is not None) == expected["expects_hypothesis"]
        ),
    }
    if expected_cause is not None:
        checks["unique_top_rank_matches_label"] = leaders == [expected_cause]
    return {
        "checks": checks,
        "resolved_claims": resolved_claims,
        "total_claims": len(claims),
        "missing_expected_evidence": missing,
        "passed": all(checks.values()),
    }


@tracer.start_as_current_span(
    "opspilot.eval", record_exception=False, set_status_on_exception=False
)
def evaluate_replay(captures: Path, ground_truth: Path) -> dict:
    raw = ground_truth.read_bytes()
    digest = sha256(raw).hexdigest()
    expectations = json.loads(raw)
    if not isinstance(expectations, dict) or set(expectations) != set(SCENARIOS):
        raise ValueError(f"{ground_truth}: expected exactly the supported scenarios")
    cases = {}
    for scenario in SCENARIOS:
        expected = expectations[scenario]
        if (
            not isinstance(expected, dict)
            or not isinstance(expected.get("service"), str)
            or not isinstance(expected.get("expects_hypothesis"), bool)
            or not isinstance(expected.get("expected_records"), list)
            or not expected["expected_records"]
            or not all(
                isinstance(target, dict) and target
                for target in expected["expected_records"]
            )
        ):
            raise ValueError(f"{ground_truth}: invalid expectations for {scenario}")
        with tracer.start_as_current_span(
            "opspilot.eval.scenario",
            attributes={
                "opspilot.scenario": scenario,
                "opspilot.eval.ground_truth_sha256": digest,
                "langfuse.observation.type": "evaluator",
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            result = score_report(investigate(scenario, captures), expected)
            scores = {
                "passed": result["passed"],
                "resolved_claims": result["resolved_claims"],
                "total_claims": result["total_claims"],
                **result["checks"],
            }
            span.set_attributes(
                {f"opspilot.eval.{key}": value for key, value in scores.items()}
            )
            span.set_attribute("langfuse.observation.output", json.dumps(scores))
            cases[scenario] = result
    return {
        "scenarios": cases,
        "passed_scenarios": sum(result["passed"] for result in cases.values()),
        "total_scenarios": len(cases),
    }
