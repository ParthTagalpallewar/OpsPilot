# Container packaging and continuous integration

An image packages the application and its runtime dependencies. The Dockerfile installs locked dependencies before copying the project code, so Docker can reuse the dependency layer when only the source changes. The runtime user has write access to `/data`, which is where the API and worker share a SQLite database.

Compose starts two containers from the same image. The API exposes a loopback port and the worker processes jobs from the shared volume. The worker waits for the API health check before starting. The volume persists across container replacement and ordinary shutdown.

Continuous integration runs lint, formatting, tests, and replay evaluation from a clean checkout. A second job builds the image and checks that an HTTP request reaches the API, creates a persisted job, and produces a completed report through the separate worker.

## Practice

Start the demo using the README, run the smoke script, then stop and restart the stack with its volume intact. Retrieve the earlier investigation ID to verify that the report survived.

## Run the shared-backend variant

The shared Compose overlay extends the same demo with PostgreSQL and Redis. The API and worker use an image built with the optional client dependencies. Compose gives the services internal hostnames and waits for their health checks before it brings up the API. Only the API publishes a host port.

The CI smoke matrix exercises both storage modes with the same HTTP flow. The shared variant also checks the database for both approval plan graph threads, one for the original version and one for its replacement.
