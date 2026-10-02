# Features

This page summarizes the connected product flows and their current boundaries.

## Available

- **Cube model:** TypeScript packages represent cube state, apply face moves, parse basic notation, and validate states.
- **3D view:** The renderer displays a cube state and supports interactive viewing.
- **Dashboard:** Manual face editing submits typed face-grid state to validation and the Python solver. Returned moves are passed to the 3D player.
- **Image scanning:** Upload six face photos or use the live camera. OpenCV detects each face; the builder and cubie validator reject incomplete or impossible states.
- **Real-time scanning:** WebSocket binary frames return progress, requested face, confidence, retry/cancel events, and validated completion.
- **Persistence:** The guest profile, solve history, DNF and +2 penalties, statistics, and training recognition/execution times are stored through the API.
- **API foundation:** FastAPI provides health, validate, solve, scan, coaching, profile, solve-record, statistics, training, and WebSocket routes.
- **Deployment:** Compose defines PostgreSQL, FastAPI, and the Next.js development target; Alembic applies database migrations.
- **Python tools:** `ai/engine` and `ai/vision` contain standalone cube and scanning workflows.

## Remaining limits

- The guest profile is local and unauthenticated; multi-user identity and access control are not implemented.
- Training attempts store timing and correctness, but do not yet provide personalized progression plans.
- External coaching requires a compatible endpoint configured with `COACHING_EXTERNAL_URL`.
- Docker Compose syntax is verified, but runtime startup could not be checked because Docker Desktop was unavailable.
- Playwright covers generated six-face image upload through solution playback; physical camera use still depends on browser permission and device access.

For endpoint details, see [API](api.md). For the module boundaries, see [Architecture](architecture.md).