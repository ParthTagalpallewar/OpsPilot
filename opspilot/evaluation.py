"""Score frozen replay reports against independent expectations."""

import json
from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from opspilot.replay import SCENARIOS, investigate
from opspilot.telemetry import tracer


def matched_log_span(claim_records: list[dict]) -> tuple[str, str] | None:
    if len(claim_records) != 2:
        return None
    kinds = {record.get("type"): record for record in claim_records}
    log, span = kinds.get("log_cluster"), kinds.get("trace_error")
    if log is None or span is None:
        return None
    if any(
        row.get("trace_id") == span["trace_id"]
        and row.get("span_id") == span["span_id"]
        for row in log["records"]
    ):
        return log["id"], span["id"]
    return None


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

    records = {record["id"]: record for record in report["evidence"]}
    linked_pairs = set()
    cited_ids = set()
    resolved_claims = 0
    for claim in claims:
        ids = claim["evidence_ids"]
        if ids and all(counts[evidence_id] == 1 for evidence_id in ids):
            resolved_claims += 1
            cited_ids.update(ids)
            pair = matched_log_span([records[key] for key in ids])
            if pair is not None:
                linked_pairs.add(pair)

    missing = [
        target
        for target in expected["expected_records"]
        if not any(
            record["id"] in cited_ids
            and all(record.get(key) == value for key, value in target.items())
            for record in report["evidence"]
        )
    ]
    forbidden = [
        target
        for target in expected.get("forbidden_records", [])
        if any(
            all(record.get(key) == value for key, value in target.items())
            for record in report["evidence"]
        )
    ]
    checks = {
        "service": report["service"] == expected["service"],
        "citation_resolution": (
            (bool(claims) or expected.get("expected_claims") == 0)
            and resolved_claims == len(claims)
        ),
        "expected_evidence_cited": not missing,
        "hypothesis_presence": (
            (hypothesis is not None) == expected["expects_hypothesis"]
        ),
    }
    if expected_cause is not None:
        checks["unique_top_rank_matches_label"] = leaders == [expected_cause]
    if "expected_claims" in expected:
        checks["claim_count"] = len(claims) == expected["expected_claims"]
    if "expected_log_span_links" in expected:
        checks["log_span_links"] = (
            len(linked_pairs) == expected["expected_log_span_links"]
        )
    if "forbidden_records" in expected:
        checks["forbidden_evidence_absent"] = not forbidden
    if "expected_top_causes" in expected:
        actual_keys = sorted(json.dumps(cause, sort_keys=True) for cause in leaders)
        expected_keys = sorted(
            json.dumps(cause, sort_keys=True)
            for cause in expected["expected_top_causes"]
        )
        checks["top_rank_matches_label_set"] = actual_keys == expected_keys
        checks["cause_abstention_on_tie"] = (
            hypothesis is not None and hypothesis["cause"] is None
        )
    return {
        "checks": checks,
        "resolved_claims": resolved_claims,
        "total_claims": len(claims),
        "missing_expected_evidence": missing,
        "unexpected_evidence": forbidden,
        "passed": all(checks.values()),
    }


@tracer.start_as_current_span(
    "opspilot.eval", record_exception=False, set_status_on_exception=False
)
def evaluate_replay(captures: Path, ground_truth: Path) -> dict:
    raw = ground_truth.read_bytes()
    digest = sha256(raw).hexdigest()
    expectations = json.loads(raw)
    if not isinstance(expectations, dict) or not expectations:
        raise ValueError(f"{ground_truth}: expected a nonempty mapping of replay cases")
    cases = {}
    for case, expected in expectations.items():
        if (
            not isinstance(expected, dict)
            or not isinstance(expected.get("service"), str)
            or not isinstance(expected.get("expects_hypothesis"), bool)
            or not isinstance(expected.get("expected_records"), list)
            or (
                not expected["expected_records"]
                and expected.get("expected_claims") != 0
            )
            or not all(
                isinstance(target, dict) and target
                for target in expected["expected_records"]
            )
        ):
            raise ValueError(f"{ground_truth}: invalid expectations for {case}")
        scenario = expected.get("scenario", case)
        if scenario not in SCENARIOS:
            raise ValueError(f"{ground_truth}: unknown replay scenario for {case}")
        case_captures = captures / expected.get("capture_dir", ".")
        cutoff = expected.get("as_of")
        as_of = datetime.fromisoformat(cutoff) if cutoff is not None else None
        with tracer.start_as_current_span(
            "opspilot.eval.scenario",
            attributes={
                "opspilot.scenario": scenario,
                "opspilot.eval.case": case,
                "opspilot.eval.ground_truth_sha256": digest,
                "langfuse.observation.type": "evaluator",
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            result = score_report(
                investigate(scenario, case_captures, as_of=as_of), expected
            )
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
            cases[case] = result
    return {
        "scenarios": cases,
        "passed_scenarios": sum(result["passed"] for result in cases.values()),
        "total_scenarios": len(cases),
    }
