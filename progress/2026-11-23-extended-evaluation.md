# 2026-11-23 · Extended replay evaluation

Added four evaluation cases covering a healthy metric comparison, tied deployment and flag timing, a pre-onset historical cutoff, and the measured Checkout-to-Payment incident. The harness now supports named cases over different capture directories and cutoff timestamps. The Checkout case checks measured request counts and six distinct cited log-span pairs with exact identifier matches.

Configured CI to run both the three baseline and four extended cases. The healthy and ambiguous samples are synthetic regression fixtures. This suite measures replay behavior on known cases, and live model scoring remains pending.

See the [evaluation lesson](../Concepts/04-replay-evaluation.md).
