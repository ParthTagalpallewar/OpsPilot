# 2026-11-22 · Alertmanager intake

Added `POST /v1/webhooks/alertmanager` for tagged demo alerts. The endpoint starts a queued replay for supported firing alerts and reports ignored alerts. SQLite deduplicates redelivery using the alert fingerprint and UTC start time, in the same transaction that writes the investigation and its job.

Verified concurrent duplicate delivery with equivalent time zones, distinct later occurrences, and filtering for resolved and unsupported alerts. The endpoint routes to frozen scenarios. Live Prometheus evidence acquisition remains pending.

See the [webhook lesson](../Concepts/14-alertmanager-webhooks.md).
