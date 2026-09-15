<div align="center">

# CubeAI

> AI-Powered Rubik's Cube Intelligence Platform

**An end-to-end Rubik's Cube platform combining a standalone cube engine, intelligent solving algorithms, interactive 3D simulation, computer vision scanning, speedcubing analytics, and an AI-powered coaching experience.**

CubeAI is designed to go beyond traditional online cube solvers. Instead of simply returning a sequence of moves, the platform aims to help users **understand, visualize, practice, and improve** how they solve the cube.

[Explore the Project](#./docs/overview/) · [Architecture](./docs/architecture/) · [Features](#./docs/features/) · [Getting Started](#-getting-started) · [Roadmap](#-roadmap)

[Report Bug](https://github.com/mhdhamka/CubeAI/issues) · [Request Feature](https://github.com/mhdhamka/CubeAI/issues)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6?logo=typescript)
![Next.js](https://img.shields.io/badge/Next.js-14.x-black?logo=next.js)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

</div>

---

# Architecture Principles

CubeAI is being designed around several engineering principles.

### 1. Core Logic Is Framework Independent

The cube engine should not depend directly on:

* React
* Next.js
* Three.js
* FastAPI
* OpenCV

This allows the domain logic to be tested and reused independently.

### 2. The Cube State Is the Source of Truth

Every system works with a validated representation of the cube.

```text
Camera ──────┐
Manual Input ├──► CubeState ◄── Solver
3D Renderer ─┘       │
                     ▼
                 Validation
```

### 3. Services Should Be Replaceable

The solver, AI provider, computer vision implementation, or frontend should be replaceable without rewriting the entire platform.

### 4. Visualization Is Separate From Simulation

The 3D engine is responsible for presenting the cube visually. The Cube Core Engine remains responsible for determining what the cube actually looks like.

---

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

For detailed Docker configuration, deployment commands, and troubleshooting, see:

* `DOCKER-QUICKSTART.md`
* `DOCKER-DEPLOYMENT.md`
* `phase-10-docker.md`
* `PHASE-10-README.md`

```

That's the actual integration you need: **Docker becomes the recommended full-stack setup, while the existing local Next.js/Python setup stays available for development.**
```
---

# Testing Strategy

Because cube manipulation logic is highly state-dependent, testing is a critical part of the project.

The Cube Core Engine should be tested independently from the UI.

### Core Test Examples

* A move followed by its inverse restores the original state.
* Four quarter turns restore the original state.
* Scrambled cubes contain valid piece configurations.
* Invalid sticker configurations are rejected.
* Move sequences produce deterministic results.
* Serialization preserves the cube state.

Example concept:

```text
R + R' = Solved State

R R R R = Solved State

Algorithm + Inverse Algorithm = Original State
```

Testing categories include:

* **Unit Tests** — Individual moves, parsers, validators, and utilities
* **Integration Tests** — Communication between packages and services
* **End-to-End Tests** — Complete user workflows
* **Visual Testing** — 3D rendering and animation behavior
* **Validation Testing** — Detection of impossible cube states

---

# Contributing

Contributions, ideas, and feedback are welcome as the project evolves.

If you find a bug or have an idea that could improve CubeAI:

1. Check the existing issues.
2. Open a bug report or feature request.
3. Clearly describe the expected behavior or proposed improvement.

For larger contributions, please open an issue first to discuss the proposed architecture or implementation.

---

# License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more information.

---

<div align="center">

### CubeAI

**Scan it. Understand it. Solve it. Master it.**

If you find this project interesting, consider giving the repository a .

Built as an experimental engineering project by **mhdhamka** 

</div>
