"""Plan construction and validation for local dry-run review."""

import json
from datetime import datetime, timedelta
from hashlib import sha256
from uuid import uuid4


class ApprovalConflict(ValueError):
    pass


def make_plan(action: str, evidence_ids: list[str], now: datetime) -> dict:
    plan = {
        "plan_id": str(uuid4()),
        "action": action,
        "evidence_ids": evidence_ids,
        "mode": "dry_run",
        "expires_at": (now + timedelta(hours=1)).isoformat(),
    }
    digest = sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    return {**plan, "plan_hash": digest}


def preview_plan(plan: dict) -> dict:
    """Describe the approved follow-up without invoking any external operation."""
    return {
        "mode": "dry_run",
        "status": "preview_ready",
        "plan_id": plan["plan_id"],
        "plan_hash": plan["plan_hash"],
        "planned_action": plan["action"],
        "evidence_ids": list(plan["evidence_ids"]),
        "executed_actions": [],
    }
