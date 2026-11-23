# Rollout activity as incident evidence

A Kubernetes Deployment creates or reuses ReplicaSets to manage versions of its Pod template. A ReplicaSet export includes a creation timestamp, an owner reference, and often a revision annotation. OpsPilot uses the controlling Deployment and namespace to select records. It stores the source item location so a reviewer can check the timing.

A ReplicaSet creation timestamp tells you when the object was created. Pod readiness and successful traffic require separate evidence. A rollback can reuse an earlier ReplicaSet, so this method can miss a rollout that creates no new object. Retention settings can also remove historical ReplicaSets.

When a creation event fits between the baseline and the first elevated sample, replay can rank the rollout as a possible contributor. A flag update in the same interval can tie with it. Check which Pods received traffic, compare errors by revision, and look for recovery after an operator changes course.

## Practice

Export ReplicaSets from a local test cluster using the README instructions. Inspect which rows the importer retains. Compare the creation time with the first anomalous sample and explain what extra data would help verify its impact.
