"""Stream durable investigation status updates."""

import json
from collections.abc import AsyncIterator

import anyio

from opspilot.investigations import InvestigationStore

TERMINAL = {"completed", "failed"}


async def status_events(
    store: InvestigationStore, investigation_id: str, cursor: int, initial: dict
) -> AsyncIterator[str]:
    yield ": connected\n\n"
    idle_polls = 0
    while True:
        events = await anyio.to_thread.run_sync(
            store.events_after, investigation_id, cursor
        )
        for event in events:
            cursor = event["id"]
            name = "step" if "step" in event else "status"
            yield f"id: {cursor}\nevent: {name}\ndata: {json.dumps(event)}\n\n"
            if event["status"] in TERMINAL:
                return

        if events:
            idle_polls = 0
            continue

        if initial["status"] in TERMINAL:
            # Older records have no events. Reconnecting after completion exits too.
            if cursor == 0:
                payload = json.dumps({"status": initial["status"]})
                yield f"event: status\ndata: {payload}\n\n"
            return

        idle_polls += 1
        if idle_polls % 15 == 0:
            yield ": keep-alive\n\n"
        await anyio.sleep(1)
