# Docker Status

## Present

- `Dockerfile` builds the Python API image.
- `Dockerfile.web` builds and runs the Next.js app.
- `docker-compose.yml` defines PostgreSQL, API, and web services, including health checks, Alembic migrations, source mounts, and a persistent database volume.

## Needs attention

- `docker compose config` parses the current configuration.
- Container startup could not be verified because Docker Desktop's Linux engine is unavailable in this environment.

Use the example credentials locally only. Replace them, enable HTTPS, and configure production CORS before deployment.