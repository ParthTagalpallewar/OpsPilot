# Alertmanager webhooks and idempotency

Alertmanager can send a notification with multiple alerts. OpsPilot examines each alert's own status. A firing alert with a recognized `opspilot_scenario` label queues the corresponding frozen demo replay.

Webhooks can be delivered more than once. OpsPilot combines the alert fingerprint with its start time in UTC to identify an occurrence. A later occurrence can reuse the fingerprint and still create a new investigation because its start time differs.

The occurrence key, investigation, and job are written in one database transaction. Concurrent requests serialize the check and insert, so both responses reference the same investigation. If a multi-alert delivery stops partway through, the sender can retry it and existing keys are reused.

## Practice

Post a group containing one firing alert, one resolved alert, and one firing alert with an unknown scenario. Check the investigation list and ignored count. Send the same group again and compare the IDs. Then change the firing alert's start time to model a recurrence.

See the [Prometheus notification reference](https://prometheus.io/docs/alerting/latest/notifications/).
