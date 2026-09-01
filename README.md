<div align="center">

# CubeAI

### AI-Powered Rubik's Cube Intelligence Platform

**An end-to-end Rubik's Cube platform combining a standalone cube engine, intelligent solving algorithms, interactive 3D simulation, computer vision scanning, speedcubing analytics, and an AI-powered coaching experience.**

CubeAI is designed to go beyond traditional online cube solvers. Instead of simply returning a sequence of moves, the platform aims to help users **understand, visualize, practice, and improve** how they solve the cube.

[Explore the Project](#-overview) · [Architecture](#-system-architecture) · [Features](#-key-features) · [Getting Started](#-getting-started) · [Roadmap](#-roadmap)

[Report Bug](https://github.com/mhdhamka/CubeAI/issues) · [Request Feature](https://github.com/mhdhamka/CubeAI/issues)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6?logo=typescript)
![Next.js](https://img.shields.io/badge/Next.js-14.x-black?logo=next.js)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

</div>

---

## Overview

**CubeAI** is an experimental, full-stack platform exploring how modern software engineering, computer vision, artificial intelligence, and interactive 3D technologies can be combined to create a more intelligent Rubik's Cube experience.

Most existing cube solvers focus on a single interaction:

> **Enter cube state → Receive moves → Solve cube**

CubeAI expands this workflow into a complete learning and analysis ecosystem:

> **Scan → Validate → Understand → Solve → Visualize → Practice → Analyze → Improve**

The platform is built around a fundamental architectural principle: **the Rubik's Cube logic should not depend on the user interface, camera system, solver, or AI services**.

At the center of the project is a standalone **Cube Core Engine** responsible for representing and manipulating cube states. Other systems—including the solver, 3D renderer, computer vision scanner, and AI coach—interact with the same underlying domain model.

This approach allows CubeAI to grow from a web application into a reusable Rubik's Cube technology ecosystem.

---

## Project Vision

CubeAI aims to answer a simple question:

> **What would a modern Rubik's Cube platform look like if solving, visualization, computer vision, analytics, and AI coaching were designed as one integrated system?**

The long-term goal is to support multiple types of users:

| User                      | CubeAI Experience                                                           |
| ------------------------- | --------------------------------------------------------------------------- |
| **Beginner**           | Learn how the cube works through guided tutorials and visual explanations   |
| **Learner**            | Practice algorithms, understand notation, and receive step-by-step guidance |
| **Speedcuber**          | Track solve times, session statistics, averages, and performance trends     |
| **Physical Cube User** | Scan a real cube using a camera instead of manually entering sticker colors |
| **Advanced Solver**    | Analyze move sequences, algorithms, and alternative solving paths           |
| **Developer**          | Reuse the standalone cube engine and related packages in other applications |

---

# System Architecture

CubeAI follows a modular architecture where the core cube domain is isolated from presentation and external services.

```text

                         ┌───────────────────────────┐
                         │          CubeAI           │
                         │  Rubik's Cube Platform    │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │       Next.js Web         │
                         │                           │
                         │  React / TypeScript       │
                         │  3D Renderer              │
                         │  Scanner UI               │
                         │  Solver UI                │
                         │  Dashboard                │
                         └─────────────┬─────────────┘
                                       │
                              REST / WebSocket
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │      FastAPI API          │
                         │      Python 3.11          │
                         │                           │
                         │  /solve                   │
                         │  /validate                │
                         │  /scan/image              │
                         │  /solves                  │
                         │  /health                  │
                         │  WebSocket Scan Sessions  │
                         └──────┬───────────┬────────┘
                                │           │
                    ┌───────────┘           └──────────────┐
                    ▼                                      ▼
          ┌───────────────────┐                  ┌───────────────────┐
          │   Python AI Layer │                  │    PostgreSQL      │
          │                   │                  │                   │
          │ Vision Scanner    │                  │ Profiles          │
          │ Color Detection   │                  │ Solves            │
          │ CubeStateBuilder  │                  │ Sessions          │
          │ CubeValidator     │                  │ Statistics        │
          │ Solver Bridge     │                  │ Training Data     │
          │ AI Coach          │                  │                   │
          └─────────┬─────────┘                  └───────────────────┘
                    │
                    ▼
          ┌───────────────────┐
          │    Cube Core      │
          │                   │
          │ CubeState         │
          │ Move Engine       │
          │ Validation        │
          │ Notation          │
          │ Scrambler         │
          └───────────────────┘
```

# Containerized Architecture

The development and deployment environment is organized into three primary services:

┌──────────────────────────────────────────────────────────────┐
│                        Docker Compose                        │
│                                                              │
│  ┌────────────────┐       ┌────────────────┐                 │
│  │ cube-ai-web    │       │ cube-ai-api    │                 │
│  │                │       │                │                 │
│  │ Next.js        │──────►│ FastAPI        │                 │
│  │ Node.js 18     │ REST  │ Python 3.11    │                 │
│  │ Port 3000      │ WS    │ Port 8000      │                 │
│  └────────────────┘       └───────┬────────┘                 │
│                                   │                          │
│                                   ▼                          │
│                          ┌────────────────┐                  │
│                          │ cube-ai-       │                  │
│                          │ postgres       │                  │
│                          │                │                  │
│                          │ PostgreSQL 14  │                  │
│                          │ Port 5432      │                  │
│                          └───────┬────────┘                  │
│                                  │                           │
│                           postgres-data                      │
│                             persistent                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Core Data Flow

A typical CubeAI solving session may follow this workflow:

```text
Physical Rubik's Cube
        │
        ▼
  Camera / Scanner
        │
        ▼
Color & Sticker Detection
        │
        ▼
  Cube State Reconstruction
        │
        ▼
  Cube State Validation
        │
        ├── Invalid → Request correction
        │
        ▼
  Solver Engine
        │
        ▼
  Solution Sequence
        │
        ├───────────────────┐
        ▼                   ▼
  3D Solution Playback    AI Coach
        │                   │
        ▼                   ▼
User Visualization      Explanation & Feedback
        │                   │
        └─────────┬─────────┘
                  ▼
              PostgreSQL
                  │
                  ▼
          Progress & Insights
```

---

# Key Features

## Standalone Cube Core Engine

The Cube Core Engine is the foundation of CubeAI.

Rather than embedding Rubik's Cube logic directly inside React components or API endpoints, cube operations are implemented as a standalone domain package.

### Responsibilities

* Cube state representation
* Face rotations
* Standard move execution
* Whole-cube rotations
* Move inversion
* Move sequences and algorithms
* Scramble generation
* Cube state validation
* Serialization and deserialization
* Integration with solver and renderer packages

### Supported Move Concepts

The engine is designed to support standard Singmaster notation:

```text
R   Right clockwise
R'  Right counter-clockwise
R2  Right double turn

U   Up clockwise
D   Down clockwise
L   Left clockwise
F   Front clockwise
B   Back clockwise
```

Future support can include:

* Wide moves (`Rw`, `Uw`, etc.)
* Slice moves (`M`, `E`, `S`)
* Cube rotations (`x`, `y`, `z`)
* Algorithm macros
* Custom notation formats

### Why a Standalone Core?

A dedicated core makes it possible for the same cube state to be used by:

* The web application
* The 3D renderer
* The solver
* Computer vision services
* AI coaching services
* Automated tests
* Future mobile applications

The cube should behave identically regardless of where it is displayed.

---

## Intelligent Solver System

CubeAI's solver subsystem is responsible for transforming a valid scrambled cube state into a sequence of legal moves.

The architecture is designed to support multiple solving strategies rather than permanently coupling the platform to one algorithm.

### Planned Solver Capabilities

* Kociemba Two-Phase solving
* Search-based solving using IDA*
* Move sequence optimization
* Alternative solution comparison
* Solution metrics
* Move count analysis
* Execution-friendly solutions

### Solver Pipeline

```text
CubeState
    │
    ▼
State Validation
    │
    ▼
Solver Selection
    │
    ├── Fast Solver
    ├── Optimal / Search Solver
    └── Educational Solver
    │
    ▼
Raw Move Sequence
    │
    ▼
Move Optimization
    │
    ▼
Solution Result
```

A solver result can contain more than just moves:

```typescript
interface SolutionResult {
  moves: string[];
  moveCount: number;
  executionTime: number;
  method: string;
  explanation?: string;
}
```

This allows the AI coaching layer and analytics system to understand the context behind a solution.

---

## Interactive 3D Cube Simulation

CubeAI uses a 3D visualization layer to make cube states and algorithms easier to understand.

Rather than showing a plain text sequence such as:

```text
R U R' U'
```

the platform can visually demonstrate each move on an interactive cube.

### Planned Capabilities

* Interactive 3D Rubik's Cube
* Mouse and touch controls
* Individual face rotations
* Smooth move animations
* Step-by-step solution playback
* Play, pause, next, and previous controls
* Algorithm demonstrations
* Camera rotation
* Scramble visualization

### Technology

The rendering layer is designed around:

* Three.js
* React Three Fiber
* TypeScript
* Shared Cube Core state

The renderer should **consume cube states rather than own cube logic**, ensuring visual animation never becomes the source of truth for the actual cube state.

---

## Computer Vision Cube Scanner

The computer vision subsystem aims to allow users to scan a physical Rubik's Cube using a camera.

The system will process captured faces and reconstruct a valid digital cube state.

### Vision Pipeline

```text
Camera Stream
      │
      ▼
Frame Processing
      │
      ▼
Cube / Face Detection
      │
      ▼
Sticker Grid Detection
      │
      ▼
Color Sampling
      │
      ▼
Color Classification
      │
      ▼
Face Reconstruction
      │
      ▼
Cube State Validation
```

### Planned Technologies

* OpenCV
* NumPy
* Custom color classification
* Geometric contour detection
* Optional MediaPipe-based vision utilities

### Key Challenges

Computer vision introduces challenges that are not present when manually entering a cube state:

* Different lighting conditions
* Sticker reflections
* Camera white balance
* Cube orientation
* Similar colors
* Shadows and occlusion
* Invalid or physically impossible states

For this reason, the scanner is treated as an input system—not the authority on cube correctness. Every reconstructed state should pass through the **Cube Core validation layer** before reaching the solver.

---

## AI Coach & Learning System

The AI Coach is intended to differentiate CubeAI from a traditional solver.

Instead of only answering:

> "Do these moves."

The system aims to explain:

> "Why are these moves being performed, what is happening to the cube, and what should you learn from this step?"

### Planned Learning Areas

#### 🟢 Beginner Learning

* Cube fundamentals
* Understanding faces and pieces
* Move notation
* First layer
* Second layer
* Beginner last-layer techniques

#### 🔵 Intermediate Learning

* CFOP fundamentals
* Cross planning
* F2L pair recognition
* Efficient finger tricks
* Lookahead concepts

#### 🟣 Advanced Training

* OLL recognition
* PLL recognition
* Algorithm optimization
* Execution efficiency
* Case recognition training

### AI Coaching Experience

```text
User Action
    │
    ▼
Cube Context + Learning Goal
    │
    ▼
AI Coaching Engine
    │
    ├── Explain
    ├── Demonstrate
    ├── Ask Questions
    ├── Identify Mistakes
    └── Recommend Practice
    │
    ▼
Personalized Feedback
```

The AI should ideally be grounded in structured cube data, algorithms, and validated cube states rather than relying solely on unrestricted text generation.

---

## Speedcubing Timer & Analytics

CubeAI will include a telemetry and statistics system for tracking solving performance.

### Planned Statistics

* Individual solve times
* Session history
* Personal best
* Mean and median
* Average of 5 (Ao5)
* Average of 12 (Ao12)
* Average of 100 (Ao100)
* Historical performance trends
* Session consistency
* Progress over time

Example session data:

```text
Session #12

Solve 1   12.42s
Solve 2   11.89s
Solve 3   13.01s
Solve 4   11.45s
Solve 5   12.10s

Ao5       12.14s
Best      11.45s
```

Future analytics may identify patterns such as:

* Performance improvements
* Consistency problems
* Training plateaus
* Algorithm-specific weaknesses

---

# Technology Stack

| Category              | Technologies                                  |
| --------------------- | --------------------------------------------- |
| **Frontend**          | Next.js, React, TypeScript                    |
| **UI & Styling**      | Tailwind CSS                                  |
| **3D Visualization**  | Three.js, React Three Fiber                   |
| **Backend Services**  | FastAPI, Python                               |
| **API Communication** | REST APIs, WebSockets                         |
| **Computer Vision**   | OpenCV, NumPy                                 |
| **AI / Intelligence** | AI coaching and structured reasoning services |
| **Cube Engine**       | TypeScript standalone packages                |
| **Solver System**     | Kociemba, IDA*, search algorithms             |
| **Testing**           | Unit, integration, and end-to-end testing     |
| **Deployment**        | Docker and containerized services             |

---

# Project Structure

CubeAI follows a monorepo-oriented structure to separate applications from reusable domain packages.

```text
CubeAI/
│
├── apps/
│   ├── web/                        # Next.js web application
│   │   ├── app/                    # Application routes
│   │   ├── components/             # Reusable UI components
│   │   ├── features/               # Feature modules
│   │   └── lib/                    # Client utilities
│   │
│   └── api/                        # FastAPI backend services
│       ├── routers/                # API endpoints
│       ├── services/               # Application services
│       ├── schemas/                # Request/response models
│       └── core/                   # Configuration and infrastructure
│
├── packages/
│   ├── cube-core/                  # Cube domain model & state engine
│   │   ├── src/
│   │   └── tests/
│   │
│   ├── cube-renderer/              # 3D visualization abstractions
│   │
│   ├── cube-solver/                # Solving algorithms & adapters
│   │
│   ├── cube-notation/              # Notation parsing & formatting
│   │
│   └── shared/                     # Shared types & constants
│
├── ai/
│   ├── vision/                     # Cube scanning pipeline
│   ├── color-classifier/           # Sticker color recognition
│   └── coach/                      # AI coaching & explanation logic
│
├── database/
│   ├── schema/                     # Database definitions
│   ├── migrations/                 # Schema migrations
│   └── seeds/                      # Development data
│
├── docs/
│   ├── architecture/               # System architecture documentation
│   ├── algorithms/                 # Solver & cube algorithm documentation
│   ├── api/                        # API specifications
│   └── decisions/                  # Architecture decision records
│
├── tests/
│   ├── integration/                # Cross-service tests
│   └── e2e/                        # End-to-end tests
│
├── docker-compose.yml
├── package.json
├── README.md
└── LICENSE
```

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

# Project Structure 

```text
CubeAI/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   └── lib/
│   └── api/
│       ├── routers/
│       ├── services/
│       ├── schemas/
│       └── core/
├── packages/
│   ├── cube-core/
│   ├── cube-renderer/
│   ├── cube-solver/
│   └── cube-notation/
├── shared/
│   ├── ai/
│   ├── vision/
│   ├── color-classifier/
│   └── coach/
├── database/
│   ├── schema/
│   ├── migrations/
│   └── seeds/
├── docs/
│   ├── architecture/
│   ├── algorithms/
│   ├── api/
│   └── decisions/
├── tests/
│   ├── integration/
│   └── e2e/
├── Dockerfile
├── Dockerfile.web
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .env.docker
├── package.json
├── README.md
└── LICENSE
```

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
