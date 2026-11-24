# 2026-11-24 · Worker lease renewal

The worker renews its job lease every 15 seconds while it collects telemetry,
runs the investigation, and saves the result. The worker stops renewing when the
job finishes or raises an exception. Renewal checks both the claim token and the
expiry timestamp. It cannot revive an expired claim. A database error during
renewal is logged and can be retried before expiry.

The queue regression test uses two SQLite store instances and advances the
clock beyond the original lease while the first worker is still running.
The second store cannot claim that job and there is only one completion.
The expiry test also checks that an old worker cannot renew after expiration.
