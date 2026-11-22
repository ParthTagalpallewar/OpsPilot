# Server-sent events and reconnects

An investigation changes from queued to running to completed or failed. Each transition and its event are committed together. This lets a client that connects after the worker finishes still see the recorded transitions.

Server-sent events use a single HTTP response with frames separated by a blank line. OpsPilot sends an `id`, an `event` name, and JSON `data`. Comment frames keep an idle connection active. A reconnect can send `Last-Event-ID` to ask for events after the last one it received.

The local API polls SQLite behind the stream. It closes after a terminal event. A reconnect that already has the terminal event receives HTTP 204. The cursor belongs to one investigation, so the server rejects a cursor from another investigation.

## Practice

Queue an incident and open its event stream before starting the worker. Save one event ID, finish the investigation, and reconnect with that ID. Check which events replay. Fetch the completed report and follow a cited ID through the investigation's evidence endpoint.

## Workflow step events

Queued workers also stream LangGraph updates while completing the report. Each completed graph node produces an SSE `step` event. Step events share cursors with lifecycle events, so a reconnect works anywhere in the stream. The database checks the worker's current claim token before it appends each step. Progress events from a reclaimed job's previous worker are discarded.
