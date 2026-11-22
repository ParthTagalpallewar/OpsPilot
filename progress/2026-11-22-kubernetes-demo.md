# 2026-11-22 · Local Kubernetes manifests

Added a Kubernetes Deployment, Service, PersistentVolumeClaim, and Kustomize entry point for the replay demo. A single Pod runs the API and worker on one volume. The Deployment uses Recreate and the Service stays inside the cluster. The README gives image loading and port-forwarding steps for a local cluster.

The manifest uses the current SQLite demo. Shared PostgreSQL and Redis deployment remains pending. No Kubernetes context is configured in this workspace, so live rollout and volume provisioning remain unverified.

See the [Kubernetes lesson](../Concepts/17-kubernetes-local-deployment.md).

Verified `kubectl kustomize infra/kubernetes` and checked the rendered selectors, port mapping, image reference, and shared volume wiring. Fourteen Python tests, Ruff, and all three replay evaluations passed.
