# Getting Started

## Requirements

- Node.js 20 or newer and npm
- Python 3.11 for the API
- PostgreSQL only if you want to use the configured database instead of SQLite

## Run the web app

From the repository root:

```bash
npm ci
npm run web:dev
```

Open <http://localhost:3000>.

## Run the API

Create and activate a virtual environment from the repository root.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-test.txt
$env:DATABASE_URL = "sqlite:///./cubeai.db"
npm run api:dev
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-test.txt
export DATABASE_URL=sqlite:///./cubeai.db
npm run api:dev
```

The API is at <http://localhost:8000>; interactive docs are at <http://localhost:8000/docs>. Alembic migrations are applied when the API starts.

## Docker

Docker Compose runs PostgreSQL, FastAPI, and the Next.js development server:

```powershell
Copy-Item .env.example .env.docker
docker compose --env-file .env.docker up --build
```

Open <http://localhost:3000>; API docs are at <http://localhost:8000/docs>. Replace example credentials before using any non-local environment. See [Docker Development](docker/docker.md).

## Next steps

- Run the checks in [Testing](testing.md).
- Browse the [API reference](api.md) and [Cube notation guide](cube-algorithms.md).
- Read [Features](features.md) for current limitations.