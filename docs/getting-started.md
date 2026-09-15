
# Getting Started

> **Note:** CubeAI is currently under active development. The recommended way to run the complete platform is through Docker Compose, which starts the frontend, FastAPI backend, and PostgreSQL database together.

## Prerequisites

Make sure you have the following installed:

* Git
* Docker Desktop
* Node.js 20+ *(only required for running the frontend outside Docker)*
* Python 3.11+ *(only required for running the API outside Docker)*

## Clone the Repository

```bash
git clone https://github.com/mhdhamka/CubeAI.git
cd CubeAI
```

---

## Option 1 — Run with Docker Compose

Docker Compose is the **recommended setup** because it starts the entire CubeAI stack:

```text
cube-ai-web       → Next.js
cube-ai-api       → FastAPI + Python
cube-ai-postgres  → PostgreSQL
```

### 1. Configure Environment

Create the Docker environment file:

```bash
cp .env.example .env.docker
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env.docker
```

Update `.env.docker` if you need to change database, API, or frontend configuration.

### 2. Build and Start

```bash
docker compose up --build
```

Or run in the background:

```bash
docker compose up --build -d
```

Docker will automatically:

1. Build the FastAPI container.
2. Build the Next.js container.
3. Start PostgreSQL.
4. Wait for PostgreSQL health checks.
5. Start the API.
6. Wait for the API health check.
7. Start the frontend.

### 3. Access the Services

| Service           | URL                        |
| ----------------- | -------------------------- |
| Frontend          | http://localhost:3000      |
| FastAPI           | http://localhost:8000      |
| API Documentation | http://localhost:8000/docs |
| PostgreSQL        | localhost:5432             |

### 4. View Service Status

```bash
docker compose ps
```

View logs:

```bash
docker compose logs
```

View logs for a specific service:

```bash
docker compose logs api
docker compose logs web
docker compose logs postgres
```

Follow logs:

```bash
docker compose logs -f
```

### Stop the Platform

```bash
docker compose down
```

To stop the platform and remove the PostgreSQL volume:

```bash
docker compose down -v
```

> **Warning:** `docker compose down -v` removes the persistent PostgreSQL data.

---

## Option 2 — Run Services Locally

Docker is recommended, but the frontend and API can also be developed independently.

### Install Frontend Dependencies

From the repository root:

```bash
npm install
```

### Run the Web Application

```bash
cd apps/web
npm run dev
```

Frontend:

```text
http://localhost:3000
```

### Run the API Service

```bash
cd apps/api
python -m venv .venv
```

Activate the virtual environment.

#### Windows

```powershell
.venv\Scripts\activate
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

API:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## Docker Configuration

The repository includes the following Docker files:

```text
Dockerfile              # FastAPI / Python 3.11
Dockerfile.web          # Next.js / Node.js 18
docker-compose.yml      # Web + API + PostgreSQL
.dockerignore           # Docker build optimization
.env.example            # Environment template
.env.docker             # Docker development configuration
apps/api/requirements.txt
```

For detailed Docker configuration, deployment commands, and troubleshooting, explore the [Docker Documentation Directory](./docs/docker/):

```text
* `DOCKER-STATUS.md`
* `DOCKER-DEPLOYMENT.md`
* `docker.md`
* `DOCKER README.md`
```

That's the actual integration you need: **Docker becomes the recommended full-stack setup, while the existing local Next.js/Python setup stays available for development.**

---
