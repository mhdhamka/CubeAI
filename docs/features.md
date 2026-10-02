# Features

This page separates working building blocks from flows that are still prototypes.

## Available

- **Cube model:** TypeScript packages represent cube state, apply face moves, parse basic notation, and validate states.
- **3D view:** The renderer displays a cube state and supports interactive viewing.
- **Dashboard:** The web app has navigation, a local timer, manual sticker editing, session statistics, and cube controls.
- **API foundation:** FastAPI provides health, validate, solve, scan, coaching, profile, solve-record, statistics, and WebSocket routes.
- **Persistence layer:** SQLAlchemy models and services target PostgreSQL; SQLite can be used for local development and tests.
- **Python tools:** `ai/engine` and `ai/vision` contain standalone cube and scanning workflows.

## Not yet connected end to end

- The dashboard currently keeps cube edits, timer records, and solution history in browser memory. It does not call the API for these flows.
- The dashboard scanner is informational UI; it does not upload an image or open a live camera session.
- The API image scan currently returns a placeholder solved cube instead of calling the Python vision pipeline.
- The API solve service currently returns a fixed placeholder sequence; it is not a solver bridge yet.
- The WebSocket endpoint simulates progress and face detections. It does not process camera frames with computer vision.
- The dashboard's coaching and statistics views are local presentation, not personalized API-backed data.

For endpoint details, see [API](api.md). For the module boundaries, see [Architecture](architecture.md).