# 2026-11-22 · Historical replay cutoff

Added `--as-of` for CLI replay and `as_of` for incident requests. Queued workers persist and restore the cutoff. The collectors filter resource samples, logs, change intervals, and spans by timestamp and compute summaries from the remaining evidence. Cutoff replays omit unversioned runbooks and logs with ambiguous time zones.

Verified that one Ad fault sample is visible at the onset timestamp and that an earlier replay abstains. The queued investigation test verifies cutoff persistence. The default replay evaluations still use all captured data. The cutoff models event time. Historical ingestion latency and versioned documentation remain unverified.

See the [historical replay lesson](../Concepts/25-historical-replay.md).
