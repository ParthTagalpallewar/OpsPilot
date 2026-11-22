"""Map an Alertmanager notification group to demo replay jobs."""

from datetime import UTC
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

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


def enqueue_alerts(notification: Notification, store: InvestigationStore) -> dict:
    investigations = {}
    ignored = 0
    for alert in notification.alerts:
        scenario = alert.labels.get("opspilot_scenario")
        if alert.status != "firing" or scenario not in SCENARIOS:
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
        )
        investigation_id = document["investigation_id"]
        investigations[investigation_id] = {
            "investigation_id": investigation_id,
            "incident_id": document["incident_id"],
            "status": document["status"],
        }
    return {"investigations": list(investigations.values()), "ignored_alerts": ignored}
