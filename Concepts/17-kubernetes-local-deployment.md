# Kubernetes workloads, services, and volumes

A Deployment reconciles the desired Pod count. The local replay Deployment runs the API and worker in one Pod so they share the same SQLite volume. Each container still has its own process and startup command. The worker can restart independently while a queued job remains in the database.

A PersistentVolumeClaim requests storage from the cluster. The claim survives a Pod replacement and mounts at `/data` for both containers. The one-replica Recreate strategy terminates the old Pod before starting the replacement, which fits the local SQLite storage model. Scaling the app across Pods calls for a shared database and queue design.

A Service gives the API a stable cluster address. Readiness controls when the endpoint is available to the Service. Port forwarding lets you exercise the demo from your machine with the same HTTP smoke script used for Compose.

## Practice

Load the demo image into a local cluster and apply the manifests. Queue an investigation, save its ID, and restart the Deployment. Retrieve the same report after rollout to verify persistence through the claim.
