
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
```text
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

