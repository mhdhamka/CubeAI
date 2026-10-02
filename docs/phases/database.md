# Persistence

The API uses SQLAlchemy models and services for users, profiles, solve records, scan sessions, and coaching records. The configured default database is PostgreSQL; SQLite is supported for local development and isolated tests.

## Main routes

- `POST /api/profiles` and `GET`, `PUT`, `DELETE /api/profiles/{id}`
- `POST /api/solves` and `GET`, `DELETE /api/solves/{id}`
- `GET /api/profiles/{id}/solves` for paginated history

Alembic applies versioned migrations on API startup. The initial migration creates tables from the SQLAlchemy models, including solve penalties and training attempts. Compose no longer imports the legacy UUID-based SQL bootstrap file, which did not match the API's ORM model.

For tests, `npm run api:test` covers profile, solve, penalty, and training persistence with SQLite. Run `npm run api:migrate` to apply migrations manually. See [API Reference](../api.md).