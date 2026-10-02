# Docker Status

## Present

- `Dockerfile` builds the Python API image.
- `Dockerfile.web` builds and runs the Next.js app.
- `docker-compose.yml` defines PostgreSQL, API, and web services, including basic health checks and a persistent database volume.

## Needs attention

- The Compose API command still uses `main:app`; the current app entrypoint is `apps.api.main:app`.
- The Compose API bind mount maps `./apps/api` to `/app`, hiding the package layout expected by the image.
- The API health check calls `requests`, which is not declared as an API dependency.
- Docker Compose startup has not been verified in this documentation pass.

Use local npm/Python commands from [Getting Started](../getting-started.md) until these items are fixed. The example database password must also be replaced before deployment.