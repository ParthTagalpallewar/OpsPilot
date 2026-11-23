"""Map an Alertmanager notification group to demo replay jobs."""

from datetime import UTC
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from opspilot.evidence.traces import valid_trace_id
from opspilot.investigations import InvestigationStore
from opspilot.replay import SCENARIOS


class Alert(BaseModel):
    status: Literal["firing", "resolved"]
    fingerprint: str = Field(pattern=r"^[0-9a-fA-F]{1,16}$")
    starts_at: AwareDatetime = Field(alias="startsAt")
    labels: dict[str, str]
    annotations: dict[str, str] = Field(default_factory=dict)


class Notification(BaseModel):
    alerts: list[Alert]


def enqueue_alerts(
    notification: Notification,
    store: InvestigationStore,
    live_scenarios: frozenset[str] = frozenset(),
) -> dict:
    investigations = {}
    ignored = 0
    for alert in notification.alerts:
        scenario = alert.labels.get("opspilot_scenario")
        mode = alert.labels.get("opspilot_mode", "replay")
        live = mode == "live"
        if (
            alert.status != "firing"
            or scenario not in SCENARIOS
            or mode not in {"live", "replay"}
            or (live and scenario not in live_scenarios)
        ):
            ignored += 1
            continue
        trace_id = None
        if live and scenario == "payment-failure":
            trace_id = alert.annotations.get("opspilot_trace_id")
            if trace_id is not None:
                trace_id = trace_id.strip().lower()
            if trace_id is not None and not valid_trace_id(trace_id):
                ignored += 1
                continue
        started = alert.starts_at.astimezone(UTC).isoformat()
        occurrence = f"{alert.fingerprint.lower()}:{started}"
        title = alert.labels.get("alertname", "").strip() or "Alertmanager alert"
        description = (
            alert.annotations.get("description", "").strip()
            or alert.annotations.get("summary", "").strip()
            or f"Replay triggered by an alert that fired at {started}."
        )
        document = store.create(
            scenario,
            title[:200],
            description[:10_000],
            queued=True,
            alert_occurrence=occurrence,
            live_alert_at=started if live else None,
            live_trace_id=trace_id,
        )
        investigation_id = document["investigation_id"]
        investigations[investigation_id] = {
            "investigation_id": investigation_id,
            "incident_id": document["incident_id"],
            "status": document["status"],
        }
    return {"investigations": list(investigations.values()), "ignored_alerts": ignored}
