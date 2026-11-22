"""Read-only LangGraph investigation of checked-in telemetry captures."""

import json
from collections.abc import Callable
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from opspilot.checkpoints import checkpoint_saver
from opspilot.evidence.changes import correlate_changes, read_changes
from opspilot.evidence.logs import summarize_logs
from opspilot.evidence.metrics import summarize_capture
from opspilot.evidence.prometheus import compare_windows
from opspilot.evidence.runbooks import retrieve_runbooks
from opspilot.evidence.traces import correlate_log_spans, read_failed_spans
from opspilot.hypotheses import rank_resource_hypotheses
from opspilot.reasoning import explain_report
from opspilot.telemetry import tracer

METRIC_SCENARIOS = {
    "ad-high-cpu": ("ad", "cpu_percent", "CPU"),
    "email-memory-leak": ("email", "mem_percent", "memory utilization"),
}

SCENARIOS = (*METRIC_SCENARIOS, "payment-failure")


class ReplayState(TypedDict):
    scenario: str
    captures: str
    with_claude: NotRequired[bool]
    as_of: NotRequired[str | None]
    service: NotRequired[str]
    windows: NotRequired[list[dict]]
    changes: NotRequired[list[dict]]
    logs: NotRequired[list[dict]]
    trace_errors: NotRequired[list[dict]]
    report: NotRequired[dict]


def replay_cutoff(state: ReplayState) -> datetime | None:
    return datetime.fromisoformat(state["as_of"]) if state.get("as_of") else None


@tracer.start_as_current_span(
    "opspilot.replay.collect_resource_evidence",
    record_exception=False,
    set_status_on_exception=False,
)
def collect_resource_evidence(state: ReplayState) -> dict:
    service, metric, _ = METRIC_SCENARIOS[state["scenario"]]
    captures = Path(state["captures"])
    cutoff = replay_cutoff(state)
    prometheus = captures / f"{service}-prometheus.json"
    if prometheus.is_file():
        windows = compare_windows(
            json.loads(prometheus.read_text(encoding="utf-8")),
            prometheus,
            service,
            metric,
            as_of=cutoff,
        )
    else:
        windows = []
        for phase in ("baseline", "fault"):
            windows.extend(
                summarize_capture(
                    captures / f"{service}-stats-{phase}.csv",
                    metric,
                    service,
                    phase,
                    as_of=cutoff,
                )
            )
    windows.sort(
        key=lambda record: (record["phase"], datetime.fromisoformat(record["start"]))
    )
    return {
        "service": service,
        "windows": windows,
        "changes": read_changes(
            captures / f"{service}-changes.csv", service, as_of=cutoff
        ),
    }


@tracer.start_as_current_span(
    "opspilot.replay.collect_payment_logs",
    record_exception=False,
    set_status_on_exception=False,
)
def collect_payment_logs(state: ReplayState) -> dict:
    captures = Path(state["captures"])
    cutoff = replay_cutoff(state)
    trace_path = captures / "payment-traces.json"
    traces = read_failed_spans(trace_path, "payment", as_of=cutoff)
    try:
        logs = summarize_logs(captures / "payment-logs.jsonl", "payment", as_of=cutoff)
    except FileNotFoundError:
        if not traces and not (cutoff is not None and trace_path.is_file()):
            raise
        logs = []
    return {"service": "payment", "logs": logs, "trace_errors": traces}


@tracer.start_as_current_span(
    "opspilot.replay.report_resources",
    record_exception=False,
    set_status_on_exception=False,
)
def report_resources(state: ReplayState) -> dict:
    windows, changes = state["windows"], state["changes"]
    service = state["service"]
    base = [record for record in windows if record["phase"] == "baseline"]
    fault = [record for record in windows if record["phase"] == "fault"]
    if len(base) > 1:
        raise ValueError("Replay requires one baseline metric series")
    if not base or not fault:
        return {
            "report": {
                "scenario": state["scenario"],
                "service": service,
                "observations": [],
                "hypothesis": None,
                "hypotheses": [],
                "limitation": (
                    "A comparison requires visible baseline and incident samples."
                ),
                "evidence": [*windows, *changes],
            },
        }
    baseline = base[0]
    _, _, label = METRIC_SCENARIOS[state["scenario"]]
    observations = [
        {
            "statement": (
                f"Mean {label} was {record['mean']:.2f}% in the "
                f"fault window ({record['variant']}) and "
                f"{baseline['mean']:.2f}% in the baseline window."
            ),
            "evidence_ids": [baseline["id"], record["id"]],
        }
        for record in fault
    ]
    aligned = correlate_changes(windows, changes)
    observations.extend(aligned)
    hypotheses = rank_resource_hypotheses(windows, changes, aligned, service, label)
    leading = [item for item in hypotheses if item["rank"] == 1]
    hypothesis = None
    if hypotheses:
        hypothesis = leading[0] if len(leading) == 1 else hypotheses[-1]
    return {
        "report": {
            "scenario": state["scenario"],
            "service": service,
            "observations": observations,
            "hypothesis": hypothesis,
            "hypotheses": hypotheses,
            "limitation": (
                "Resource readings and documented change intervals establish timing. "
                "Request traces and latency are needed to assess user impact."
            ),
            "evidence": [*windows, *changes],
        }
    }


@tracer.start_as_current_span(
    "opspilot.replay.report_payment",
    record_exception=False,
    set_status_on_exception=False,
)
def report_payment(state: ReplayState) -> dict:
    logs = state["logs"]
    traces = state["trace_errors"]
    return {
        "report": {
            "scenario": state["scenario"],
            "service": state["service"],
            "observations": [
                {
                    "statement": (
                        f"Captured {record['count']} payment log record(s) "
                        f"at {record['severity']} level."
                    ),
                    "evidence_ids": [record["id"]],
                }
                for record in logs
            ]
            + [
                {
                    "statement": (
                        f"Payment span {record['operation']} recorded error status"
                        + (
                            " with a direct parent span from "
                            f"{record['parent_service']}."
                            if record["parent_service"]
                            else "."
                        )
                    ),
                    "evidence_ids": [record["id"]],
                }
                for record in traces
            ]
            + correlate_log_spans(logs, traces),
            "hypothesis": None,
            "hypotheses": [],
            "limitation": (
                "Failure rates require "
                "total request counts. Attributing cause requires "
                "corroborating evidence."
            ),
            "evidence": [*logs, *traces],
        }
    }


def evidence_route(state: ReplayState):
    return "payment" if state["scenario"] == "payment-failure" else "resources"


@tracer.start_as_current_span(
    "opspilot.replay.attach_runbook",
    record_exception=False,
    set_status_on_exception=False,
)
def attach_runbook(state: ReplayState) -> dict:
    report = state["report"]
    symptom = report["scenario"]
    if state.get("logs"):
        symptom += " " + state["logs"][0]["message"][:300]
    if state.get("as_of"):
        return {"report": {**report, "as_of": state["as_of"], "guidance": []}}
    matches = retrieve_runbooks(
        Path(state["captures"]).parent / "runbooks",
        report["service"],
        symptom,
    )
    return {
        "report": {
            **report,
            "evidence": [*report["evidence"], *matches],
            "guidance": [
                {
                    "statement": record["heading"],
                    "evidence_ids": [record["id"]],
                }
                for record in matches
            ],
        }
    }


@tracer.start_as_current_span(
    "opspilot.replay.validate_report",
    record_exception=False,
    set_status_on_exception=False,
)
def validate_report(state: ReplayState) -> None:
    report = state["report"]
    evidence = report["evidence"]
    known = {item["id"] for item in evidence}
    if len(known) != len(evidence):
        raise ValueError("Report contains duplicate evidence IDs")

    claims = [*report["observations"], *report["guidance"]]
    claims.extend(report["hypotheses"])
    for claim in claims:
        if not claim["evidence_ids"] or not known.issuperset(claim["evidence_ids"]):
            raise ValueError("Report contains a claim without resolvable citations")


@tracer.start_as_current_span(
    "opspilot.replay.reason", record_exception=False, set_status_on_exception=False
)
def reason(state: ReplayState) -> dict:
    report = state["report"]
    return {"report": {**report, "model_explanation": explain_report(report)}}


def build_replay_graph(checkpointer=None):
    graph = StateGraph(ReplayState)
    graph.add_node("collect_resources", collect_resource_evidence)
    graph.add_node("collect_payment", collect_payment_logs)
    graph.add_node("report_resources", report_resources)
    graph.add_node("report_payment", report_payment)
    graph.add_node("retrieve_runbook", attach_runbook)
    graph.add_node("validate", validate_report)
    graph.add_node("reason", reason)
    graph.add_conditional_edges(
        START,
        evidence_route,
        {"resources": "collect_resources", "payment": "collect_payment"},
    )
    graph.add_edge("collect_resources", "report_resources")
    graph.add_edge("collect_payment", "report_payment")
    graph.add_edge("report_resources", "retrieve_runbook")
    graph.add_edge("report_payment", "retrieve_runbook")
    graph.add_edge("retrieve_runbook", "validate")
    graph.add_conditional_edges(
        "validate",
        lambda state: "reason" if state.get("with_claude") else END,
        {"reason": "reason", END: END},
    )
    graph.add_edge("reason", END)
    return graph.compile(checkpointer=checkpointer)


REPLAY_GRAPH = build_replay_graph()


def investigate(
    scenario: str,
    captures: Path,
    *,
    with_claude: bool = False,
    as_of: datetime | None = None,
    on_step: Callable[[str], None] | None = None,
    checkpoint: tuple[str, str] | None = None,
) -> dict:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown replay scenario: {scenario}")
    if as_of is not None and as_of.utcoffset() is None:
        raise ValueError("Replay cutoff requires a UTC offset")
    inputs = {
        "scenario": scenario,
        "captures": str(captures),
        "with_claude": with_claude,
        "as_of": as_of.astimezone(UTC).isoformat() if as_of is not None else None,
    }
    with tracer.start_as_current_span(
        "opspilot.replay",
        attributes={"opspilot.scenario": scenario},
        record_exception=False,
        set_status_on_exception=False,
    ):
        scope = (
            checkpoint_saver(*checkpoint) if checkpoint is not None else nullcontext()
        )
        with scope as saver:
            graph = build_replay_graph(saver) if saver is not None else REPLAY_GRAPH
            config = None
            final = inputs
            if checkpoint is not None:
                config = {"configurable": {"thread_id": checkpoint[1]}}
                saved = graph.get_state(config)
                if saved.values:
                    final = saved.values
                    if not saved.next and "report" in final:
                        return final["report"]
                    inputs = None

            durability = {"durability": "sync"} if checkpoint is not None else {}
            if on_step is None:
                return graph.invoke(inputs, config, **durability)["report"]
            for mode, data in graph.stream(
                inputs, config, stream_mode=["updates", "values"], **durability
            ):
                if mode == "values":
                    final = data
                else:
                    for step in data:
                        on_step(step)
            return final["report"]
