# Docker Development

The Compose file describes three services: PostgreSQL (`5432`), FastAPI (`8000`), and Next.js (`3000`). PostgreSQL stores its data in the named `postgres-data` volume.

## Environment

Compose automatically reads `.env`, not `.env.docker`. To use the example settings:

```powershell
Copy-Item .env.example .env.docker
```

Then pass that file explicitly:

```bash
docker compose --env-file .env.docker up --build
```

Stop containers while keeping database data:

```bash
docker compose down
```

To also delete database data, use `docker compose down -v`.

## Current blocker

The checked-in Compose API service overrides the container's package entrypoint with `main:app` and mounts `apps/api` over `/app`. The API is now a package at `apps.api.main`, so this override prevents the service from starting as configured. Use the local API instructions in [Getting Started](../getting-started.md) until the Compose command and bind mount are aligned.

The example database password is for local development only. Do not use it in a deployed environment.