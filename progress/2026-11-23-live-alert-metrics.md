# 2026-11-23 · Live Prometheus collection from alerts

Added a live mode for tagged Ad and Email alerts. The webhook stores the firing timestamp and returns HTTP 202. The worker queries two windows using operator-configured PromQL, saves the responses under the investigation ID, and reports progress. The existing frozen replay stays available by default.

The same frozen snapshot can be replayed offline. For multiple workers, point the capture directory at shared writable storage. Live alert-driven log, trace, and deployment collection remain pending.

See the [alert-driven evidence lesson](../Concepts/30-alert-driven-evidence.md).

Verified with a real temporary Prometheus server and a separate worker process. A controlled query produced baseline and incident means of 2% and 90%. The API exposed the capture step and the frozen snapshot reproduced the exact report offline. These values came from a test query. Twenty-six tests, three replay evaluations, and Ruff passed.
