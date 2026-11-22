"""Pause and resume one dry-run review per immutable plan version."""

from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from opspilot.approvals import preview_plan
from opspilot.storage import PostgresConnection


class ReviewState(TypedDict):
    plan: dict
    decision: NotRequired[str]
    preview: NotRequired[dict]


def wait_for_review(state: ReviewState) -> dict:
    plan = state["plan"]
    decision = interrupt({"plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"]})
    result = {"decision": decision}
    if decision == "approve":
        result["preview"] = preview_plan(plan)
    return result


def review_graph(connection: PostgresConnection):
    from langgraph.checkpoint.postgres import PostgresSaver

    workflow = StateGraph(ReviewState)
    workflow.add_node("wait_for_review", wait_for_review)
    workflow.add_edge(START, "wait_for_review")
    workflow.add_edge("wait_for_review", END)
    return workflow.compile(checkpointer=PostgresSaver(connection.connection))


def review_config(plan: dict) -> dict:
    return {"configurable": {"thread_id": f"approval:{plan['plan_id']}"}}


def pause_review(connection, plan: dict) -> None:
    if isinstance(connection, PostgresConnection):
        graph = review_graph(connection)
        graph.invoke({"plan": plan}, review_config(plan), durability="sync")


def resolve_review(connection, plan: dict, decision: str) -> dict | None:
    if not isinstance(connection, PostgresConnection):
        return preview_plan(plan) if decision == "approve" else None

    graph = review_graph(connection)
    config = review_config(plan)
    snapshot = graph.get_state(config)
    if not snapshot.values:
        # Plans saved before checkpointed approval can still be reviewed.
        graph.invoke({"plan": plan}, config, durability="sync")
    elif snapshot.values.get("plan") != plan or not snapshot.interrupts:
        raise RuntimeError("Saved approval workflow does not match the reviewable plan")
    result = graph.invoke(Command(resume=decision), config, durability="sync")
    if result.get("decision") != decision:
        raise RuntimeError("Approval workflow did not record the decision")
    return result.get("preview")
