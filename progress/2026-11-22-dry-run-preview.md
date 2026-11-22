# 2026-11-22 · Audited dry-run preview and portfolio demo

Approving a plan now creates a dry-run preview in the same database transaction as the approval event. The preview binds the proposed follow-up and evidence to the exact approved plan hash. The API returns it on later reads and identical approval retries.

Expanded the container smoke test to edit a plan, reject the stale hash, approve the revised version, and verify the audit history and preview. Added a [portfolio walkthrough](../docs/portfolio-demo.md) and updated the README to distinguish the current demo from the target architecture. Approval is still a separate transactional flow. Suspending and resuming the graph for human review remains pending.

Verified the full queued replay and approval sequence over HTTP against separate API and worker containers. All three evaluations also passed inside the image. Ruff and twenty-three Python tests passed.
