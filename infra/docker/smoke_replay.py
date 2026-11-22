"""Smoke-test the running Docker Compose demo."""

import json
import os
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = f"http://127.0.0.1:{os.environ.get('OPSPILOT_PORT', '8000')}"


def post_json(path: str, payload: dict) -> tuple[int, dict, str | None]:
    request = Request(
        BASE_URL + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.load(response), response.headers["Location"]
    except HTTPError as exc:
        with exc:
            return exc.code, json.load(exc), None


def verify_approval(location: str, investigation: dict) -> None:
    path = location + "/approval"
    initial = investigation["plan"]
    original = {key: initial[key] for key in ("plan_id", "plan_hash")}
    action = "Compare GetAds latency across the captured windows."
    status, edited, _ = post_json(
        path, {**original, "decision": "edit", "edits": action}
    )
    if status != 200 or "dry_run_preview" in edited:
        raise RuntimeError("Editing should produce a new reviewable plan")
    stale_status, _, _ = post_json(path, {**original, "decision": "approve"})
    if stale_status != 409:
        raise RuntimeError("Expected the stale approval to return HTTP 409")

    current = edited["plan"]
    approval = {key: current[key] for key in ("plan_id", "plan_hash")}
    status, approved, _ = post_json(path, {**approval, "decision": "approve"})
    if status != 200:
        raise RuntimeError(f"Expected HTTP 200 for approval, got {status}")
    preview = approved["dry_run_preview"]
    if (
        preview["mode"] != "dry_run"
        or preview["planned_action"] != action
        or preview["plan_hash"] != approval["plan_hash"]
        or preview["executed_actions"]
        or len(approved["approval_history"]) != 2
    ):
        raise RuntimeError("Unexpected approval preview or audit history")
    retry_status, retry, _ = post_json(path, {**approval, "decision": "approve"})
    if retry_status != 200 or retry != approved:
        raise RuntimeError("Retry should return the unchanged approval result")


def main() -> None:
    incident = {
        "scenario": "ad-high-cpu",
        "title": "Ad service CPU spike",
        "description": "Verify the packaged replay demo.",
        "queued": True,
    }
    status, _, location = post_json("/v1/incidents", incident)
    if status != 202 or location is None:
        raise RuntimeError(f"Expected HTTP 202 with a Location, got {status}")
    deadline = monotonic() + 30
    while monotonic() < deadline:
        with urlopen(BASE_URL + location, timeout=5) as response:
            investigation = json.load(response)
        if investigation["status"] == "completed":
            report = investigation["report"]
            if report["service"] != "ad" or not report["evidence"]:
                raise RuntimeError("Completed replay is missing Ad evidence")
            evidence = report["evidence"][0]
            with urlopen(
                BASE_URL + location + "/evidence/" + evidence["id"], timeout=5
            ) as response:
                if json.load(response) != evidence:
                    raise RuntimeError("Citation endpoint returned different evidence")
            with urlopen(BASE_URL + location + "/events", timeout=5) as response:
                events = response.read()
                if b'"step": "validate"' not in events:
                    raise RuntimeError("Status stream omitted the validation step")
                if b'"status": "completed"' not in events:
                    raise RuntimeError("Status stream omitted the completed event")
            verify_approval(location, investigation)
            print(f"Verified replay and approval {investigation['investigation_id']}")
            return
        if investigation["status"] == "failed":
            raise RuntimeError(investigation["error"])
        sleep(0.5)
    raise TimeoutError("The worker did not complete the queued replay")


if __name__ == "__main__":
    main()
