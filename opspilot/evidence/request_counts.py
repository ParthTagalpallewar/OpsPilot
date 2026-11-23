"""Summarize counts measured by the controlled Payment capture client."""

import json
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from opspilot.evidence.error_analysis import calculate_error_rate


class RequestWindow(BaseModel):
    phase: Literal["baseline", "fault"]
    start: AwareDatetime
    end: AwareDatetime
    total: int = Field(gt=0)
    failed: int = Field(ge=0)
    statuses: dict[str, int]

    @model_validator(mode="after")
    def check_counts(self):
        if (
            self.start > self.end
            or any(value < 0 for value in self.statuses.values())
            or sum(self.statuses.values()) != self.total
            or self.total - self.statuses.get("ok", 0) != self.failed
        ):
            raise ValueError("Invalid request window or inconsistent status counts")
        return self


def read_payment_counts(path: Path, *, as_of=None) -> list[dict]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    try:
        if not isinstance(payload, dict):
            raise ValueError
        target_service = payload.get("target_service", "payment")
        if target_service not in ("payment", "checkout"):
            raise ValueError
        baseline, fault = [
            RequestWindow.model_validate(item) for item in payload["windows"]
        ]
        if (
            baseline.phase != "baseline"
            or fault.phase != "fault"
            or baseline.end >= fault.start
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{path}: invalid Payment request counts") from exc

    return [
        {
            **window.model_dump(mode="json"),
            "type": "request_counts",
            "target_service": target_service,
            "id": f"ev_payment_requests_{window.phase}",
            "source": path.name,
            "failure_percent": round(
                calculate_error_rate(window.total, window.failed), 2
            ),
        }
        for window in (baseline, fault)
        if as_of is None or window.end <= as_of
    ]
