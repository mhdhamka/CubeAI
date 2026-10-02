# Docker Notes

The repository includes Dockerfiles for the API and web app plus a Compose file for PostgreSQL, API, and web services.

The Compose API override currently points to an outdated module path and its bind mount hides the package layout. As a result, the full Compose stack is not ready to use without correcting that wiring. See [Docker Development](docker.md) for details and [Deployment Notes](DOCKER-DEPLOYMENT.md) before exposing services.

For local development that works now, follow [Getting Started](../getting-started.md).