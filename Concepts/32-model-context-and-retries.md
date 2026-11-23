# Model context minimization and bounded retries

OpsPilot builds a small outbound dataset from the frozen report. It sends numeric resource summaries, the category and timing of relevant changes, and reviewed runbook text. It replaces evidence IDs with local aliases before making the request. When a response returns, OpsPilot validates the aliases and maps them back to the original citations.

An approved hash identifies each reviewed runbook section. Editing its heading or text changes the hash and excludes that version from the model context. It can still appear in the local report. User incident text, raw logs, source paths, and free-form change values stay local.

A transient network or provider error may succeed if retried. The provider client tries at most twice, waits briefly with jitter, and avoids short-loop retries when the server asks for a longer pause. Authentication errors and invalid responses return a status while the deterministic report remains available.

## Practice

Read the model request test. Identify the fields sent and removed. Trace a returned local alias back to the full evidence record.
