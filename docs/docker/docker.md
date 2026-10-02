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

The API uses Alembic migrations at startup. Compose mounts API and vision source for local reloading; the web service uses a development image with Tailwind dependencies installed.

Run the same checks as CI with:

```bash
npm run api:test
npm run test:run
npm run web:build
npm run test:e2e
```

The example database password is for local development only. Do not use it in a deployed environment.