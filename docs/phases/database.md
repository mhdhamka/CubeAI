# Persistence

The API uses SQLAlchemy models and services for users, profiles, solve records, scan sessions, and coaching records. The configured default database is PostgreSQL; SQLite is supported for local development and isolated tests.

## Main routes

- `POST /api/profiles` and `GET`, `PUT`, `DELETE /api/profiles/{id}`
- `POST /api/solves` and `GET`, `DELETE /api/solves/{id}`
- `GET /api/profiles/{id}/solves` for paginated history

The API initializes tables on startup with SQLAlchemy metadata. The repository has SQL schema and migration files, but a migration runner is not wired into application startup.

For tests, `npm run api:test` uses an in-memory SQLite database for a persistence regression check. See [API Reference](../api.md).