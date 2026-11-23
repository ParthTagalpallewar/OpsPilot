"""HTTP entry points for local replay investigations."""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from opspilot.approvals import ApprovalConflict
from opspilot.apps.api.alertmanager import Notification, enqueue_alerts
from opspilot.apps.api.auth import ApiAccess
from opspilot.apps.api.events import TERMINAL, status_events
from opspilot.investigations import InvestigationStore
from opspilot.live_metrics import configured_live_metrics
from opspilot.live_traces import configured_live_traces
from opspilot.operational_metrics import configure_metrics
from opspilot.telemetry import configure_tracing
from opspilot.triage import route_incident
from opspilot.wakeup import configured_wakeup


class IncidentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    scenario: Literal["ad-high-cpu", "email-memory-leak", "payment-failure"] | None = (
        None
    )
    service: Literal["ad", "email", "payment"] | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    queued: bool = False
    as_of: AwareDatetime | None = None


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    plan_id: UUID
    plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: Literal["approve", "reject", "edit"]
    comment: str = Field(default="", max_length=2000)
    edits: str | None = Field(default=None, min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_edits(self):
        if (self.decision == "edit") != (self.edits is not None):
            raise ValueError("Provide replacement action text only for an edit")
        return self


def create_app(
    database: Path | str,
    captures: Path,
    *,
    on_enqueue: Callable[[], None] | None = None,
    access: ApiAccess | None = None,
    live_scenarios: frozenset[str] = frozenset(),
    publish_metrics: bool = False,
) -> FastAPI:
    store = InvestigationStore(database, captures, on_enqueue=on_enqueue)
    if publish_metrics:
        configure_metrics("api", store.queue_depth)
    app = FastAPI(title="OpsPilot")
    access = access or ApiAccess()
    read_access = [Depends(access.require("operator", "reviewer"))]
    submit_access = [Depends(access.require("operator"))]
    reviewer_access = access.require("reviewer")

    @app.post(
        "/v1/incidents",
        status_code=201,
        responses={202: {"description": "Queued"}},
        dependencies=submit_access,
    )
    def create_incident(incident: IncidentRequest, response: Response) -> dict:
        try:
            scenario = incident.scenario or route_incident(
                incident.title, incident.description, incident.service
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        try:
            document = store.create(
                scenario,
                incident.title,
                incident.description,
                queued=incident.queued,
                as_of=incident.as_of,
            )
            if incident.queued:
                response.status_code = 202
            response.headers["Location"] = (
                f"/v1/investigations/{document['investigation_id']}"
            )
            return document
        except (ValueError, OSError) as exc:
            raise HTTPException(503, "Replay telemetry is unavailable") from exc

    @app.post(
        "/v1/webhooks/alertmanager",
        status_code=202,
        dependencies=[Depends(access.require("webhook"))],
    )
    def accept_alerts(notification: Notification) -> dict:
        return enqueue_alerts(notification, store, live_scenarios)

    @app.get("/v1/investigations/{investigation_id}", dependencies=read_access)
    def get_investigation(investigation_id: UUID) -> dict:
        document = store.get(str(investigation_id))
        if document is None:
            raise HTTPException(404, "Investigation not found")
        return document

    @app.get("/v1/investigations/{investigation_id}/events", dependencies=read_access)
    def stream_investigation(
        investigation_id: UUID,
        last_event_id: Annotated[int, Header(ge=0, le=2**63 - 1)] = 0,
    ) -> Response:
        document = store.get(str(investigation_id))
        if document is None:
            raise HTTPException(404, "Investigation not found")
        if last_event_id:
            events = store.events_after(str(investigation_id), last_event_id - 1)
            if not events or events[0]["id"] != last_event_id:
                raise HTTPException(
                    400, "Event cursor does not match this investigation"
                )
            if events[0]["status"] in TERMINAL:
                return Response(status_code=204)
        return StreamingResponse(
            status_events(store, str(investigation_id), last_event_id, document),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get(
        "/v1/investigations/{investigation_id}/evidence/{evidence_id}",
        dependencies=read_access,
    )
    def get_evidence(investigation_id: UUID, evidence_id: str) -> dict:
        document = store.get(str(investigation_id))
        report = document.get("report") if document else None
        if report is not None:
            for record in report["evidence"]:
                if record["id"] == evidence_id:
                    return record
        raise HTTPException(404, "Evidence not found")

    @app.post("/v1/investigations/{investigation_id}/approval")
    def review_investigation(
        investigation_id: UUID,
        request: ApprovalRequest,
        reviewer: str = Depends(reviewer_access),
    ) -> dict:
        try:
            document = store.review(
                str(investigation_id),
                request.model_dump(mode="json"),
                reviewer=reviewer,
            )
        except ApprovalConflict as exc:
            raise HTTPException(409, str(exc)) from exc
        if document is None:
            raise HTTPException(404, "Investigation not found")
        return document

    return app


def local_app() -> FastAPI:
    configure_tracing()
    live_metrics = configured_live_metrics()
    live_scenarios = set(live_metrics.queries) if live_metrics else set()
    if configured_live_traces():
        live_scenarios.add("payment-failure")
    credentials = os.environ.get("OPSPILOT_API_CREDENTIALS")
    return create_app(
        os.environ.get("OPSPILOT_DATABASE_DSN")
        or Path(os.environ.get("OPSPILOT_DB", "opspilot.sqlite3")),
        Path(os.environ.get("OPSPILOT_CAPTURES", "testbed/scenarios")),
        on_enqueue=configured_wakeup().notify,
        publish_metrics=True,
        live_scenarios=frozenset(live_scenarios),
        access=ApiAccess.from_file(
            Path(credentials) if credentials is not None else None
        ),
    )
