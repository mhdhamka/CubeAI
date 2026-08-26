# Epic 8: Platform Integration and Later Improvements

**Status:** Proposed  
**Owner:** CubeAI team

## Goal

Connect the Next.js frontend to the Python vision and solver services, then add the persistence, real-time communication, AI coaching, testing, and deployment foundations needed for a complete CubeAI product.

## Current Gaps

- `apps/api` does not yet contain a FastAPI implementation.
- The frontend does not call an API; its solver currently uses a local inverse move history.
- Camera and image scanning are available through Python CLI workflows, not the web application.
- Python `ai/vision` and `ai/engine` are not exposed as service endpoints.
- Solve history, profiles, and statistics are currently in browser memory only.
- `docker-compose.yml` is empty.
- No WebSocket session or live scan transport exists.
- The dashboard uses CSS Modules; Tailwind is not configured yet.
- AI coaching is currently deterministic Python logic, without a separate reasoning service.
- End-to-end frontend-to-backend coverage is not yet present.

## Issues

### 1. [Integration] Frontend to API Contract

Create a typed REST client and API contract for:

- `POST /api/solve`
- `POST /api/validate`
- `POST /api/scan/image`
- `GET /api/health`
- `GET /api/solves`
- `POST /api/solves`

The contract must support CubeState, solver moves, validation errors, confidence, and scan metadata.

### 2. [Backend] FastAPI Service

Implement `apps/api` as a FastAPI service with configuration, health checks, request validation, CORS, structured errors, and service boundaries for vision, engine, and coaching operations.

### 3. [AI] Python Vision and Solver Bridge

Expose the existing Python pipeline through the API:

```text
image or camera frame
  -> ai/vision scanner
  -> CubeStateBuilder
  -> CubeValidator
  -> cubieConverter
  -> ai/engine solver
  -> validated solution
```

The API must reject incomplete or physically invalid cube states and return actionable diagnostics.

### 4. [Realtime] Camera and Scan Sessions

Add a WebSocket or streaming endpoint for live camera sessions. Support scan progress, requested face, detection confidence, retry/cancel events, and completed validated CubeState output.

### 5. [Persistence] Profiles, Solves, and Statistics

Connect the existing database schema to a persistence service for:

- user profiles
- solve records
- scrambles and solutions
- penalties and DNF results
- session history
- Ao5, Ao12, and Ao100 aggregates
- training attempts and recognition times

### 6. [Frontend] Production API Integration

Replace local placeholder behavior in `apps/web` with API-backed flows:

- scanner uploads or camera session
- solver requests
- returned solution playback
- server-backed solve history
- profile and statistics loading
- loading, retry, offline, and error states

### 7. [UI] Tailwind Design System Migration

Configure Tailwind CSS and extract reusable dashboard primitives while preserving the current Cube Lab visual language. Keep the 3D renderer package independent from UI styling.

### 8. [AI] Coaching Service

Expose contextual explanations, mistake analysis, algorithm training, and personalized recommendations through a stable API. Keep deterministic coaching as the fallback when an external reasoning service is unavailable.

### 9. [Testing] Cross-Layer Verification

Add tests for:

- FastAPI endpoint contracts
- scanner-to-builder integration
- solver request/response behavior
- frontend API client behavior
- WebSocket scan sessions
- database persistence
- Playwright end-to-end flows

Required end-to-end scenario:

```text
frontend image upload
  -> API
  -> Python vision
  -> validated CubeState
  -> Python solver
  -> solution response
  -> 3D playback in frontend
```

### 10. [Deployment] Containerized Development and CI

Complete Docker Compose for web, API, database, and optional ML services. Add environment configuration, service health checks, migrations, and CI jobs for frontend, Python, integration, and end-to-end tests.

## Technology Alignment

| Category | Target technology |
|---|---|
| Frontend | Next.js, React, TypeScript |
| UI and styling | Tailwind CSS |
| 3D visualization | Three.js, React Three Fiber |
| Backend | FastAPI, Python |
| API communication | REST APIs, WebSockets |
| Computer vision | OpenCV, NumPy |
| AI intelligence | Coaching and structured reasoning services |
| Cube engine | TypeScript standalone packages |
| Solver | Kociemba, IDA*, search algorithms |
| Testing | Unit, integration, Playwright end-to-end |
| Deployment | Docker and containerized services |

## Recommended Execution Order

1. FastAPI health endpoint and typed REST contract.
2. `/solve` and `/validate` bridge to the Python engine.
3. Frontend solver integration and real returned solutions.
4. Image upload scan endpoint.
5. WebSocket camera scan sessions.
6. Database persistence for solves and profiles.
7. Statistics and training synchronization.
8. Coaching API and reasoning provider boundary.
9. Docker Compose and CI integration tests.
10. Tailwind migration and production hardening.

## Acceptance Criteria

- The frontend can submit a cube state to the API and receive a validated solution.
- The frontend can upload an image and receive a validated CubeState with confidence data.
- A complete scan-to-solve-to-3D-playback flow works without invoking Python manually.
- Solve history and profile data survive browser refreshes and service restarts.
- Ao5, Ao12, and Ao100 are calculated from persisted solve records.
- Live scan progress supports retry and cancellation.
- Docker Compose starts the required services with health checks.
- Unit, integration, and end-to-end tests run in CI.
- API failures are shown as actionable UI states rather than silent fallbacks.
