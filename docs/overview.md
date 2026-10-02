# CubeAI Overview

CubeAI is an experimental Rubik's Cube workspace built around reusable cube logic. It combines a Next.js interface, TypeScript cube packages, a FastAPI service, and Python vision/coaching code.

## Main parts

- `apps/web`: dashboard, timer, manual sticker editor, and 3D cube view.
- `apps/api`: REST and WebSocket endpoints, service layer, and database access.
- `packages/`: reusable cube state, notation, solver, renderer, and API client code.
- `ai/`: Python cube engine, vision pipeline, and deterministic coaching logic.
- `database/`: SQL schema and migrations.

## Current status

The reusable cube packages and API services are present, and the dashboard runs locally. Some product flows are still prototypes: the dashboard does not yet use the API for solving or image upload; the API vision service returns a placeholder solved state; and the WebSocket scanner simulates detections.

Start with [Getting Started](getting-started.md), then see [Features](features.md) and [Architecture](architecture.md).