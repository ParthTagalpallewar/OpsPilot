# 2026-11-23 · Kubernetes rollout evidence

Added a read-only ReplicaSet import for the Ad and Email scenarios. It selects objects controlled by a named Deployment in one namespace, then freezes their creation timestamps and revision metadata. Replay cites rollout and flag-change records independently and applies its normal historical cutoff and change ranking.

Verified with a representative Kubernetes export fixture. The rollout and flag change tied when both fit the incident onset gap, and an earlier cutoff excluded the rollout. A live cluster export, a rollout completion signal, and alert-driven deployment fetching remain pending.

See the [rollout evidence lesson](../Concepts/31-kubernetes-rollout-evidence.md).
