# API Reference

Base URL for local development: `http://localhost:8000`. Interactive OpenAPI documentation is available at `/docs` when the API is running.

## Routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Service health |
| `GET` | `/api/health/ready` | Readiness response |
| `GET` | `/api/health/live` | Liveness response |
| `POST` | `/api/validate` | Validate a cube state |
| `POST` | `/api/solve` | Request a solution |
| `POST` | `/api/scan/image` | Upload one image as `file` or multiple face images as repeated `files` fields |
| `WS` | `/api/scan/session` | Send binary image frames; receive progress, retry, cancel, and completion events |
| `POST` | `/api/coaching` | Get contextual coaching; optional external provider with deterministic fallback |
| `POST` | `/api/profiles/guest` | Get or create the local persistent Cube Lab profile |
| `POST` | `/api/profiles` | Create a profile |
| `GET`, `PUT`, `DELETE` | `/api/profiles/{profile_id}` | Read, update, or delete a profile |
| `GET` | `/api/profiles/{profile_id}/solves` | List solves (`limit`, `offset`) |
| `GET` | `/api/solves?profile_id={id}` | List solve records for a profile |
| `POST` | `/api/solves` | Create a solve record |
| `GET`, `DELETE` | `/api/solves/{solve_id}` | Read or delete a solve |
| `GET` | `/api/profiles/{profile_id}/statistics` | Profile statistics |
| `GET` | `/api/profiles/{profile_id}/statistics/improvement` | Recent trend |
| `GET` | `/api/profiles/{profile_id}/statistics/milestones` | Personal-best milestones |
| `POST` | `/api/training` | Persist an algorithm-training attempt and recognition time |
| `GET` | `/api/profiles/{profile_id}/training` | List training attempts |

## Cube state

The API represents a 3x3 state with piece permutations and orientations:

```json
{
  "corners": [0, 1, 2, 3, 4, 5, 6, 7],
  "corner_orientations": [0, 0, 0, 0, 0, 0, 0, 0],
  "edges": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  "edge_orientations": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
}
```

Validation and solve requests wrap it in `cube_state`. They also accept the frontend face-grid form `{ "faces": { "U": [[...]], ... } }` with six row-major 3x3 faces. Both forms are physically validated by the Python cubie engine. Solve requests may include `max_moves`. Responses use moves with `face` (`U`, `D`, `F`, `B`, `L`, `R`) and `times` (`1`, `2`, or `3`, where `3` means a prime turn).

## Errors and limitations

Malformed request bodies receive FastAPI's `422` response. Domain errors use a structured `code`, `message`, and optional `details` object.

`/api/scan/image` runs the OpenCV scanner for each supplied face, builds a Python cube state, converts it to cubies, and rejects incomplete or physically invalid cubes. `/api/solve` uses Kociemba and verifies returned moves with CubeAI's move engine. WebSocket frames use the same scanner, builder, and validation path.

Set `COACHING_PROVIDER=external` and `COACHING_EXTERNAL_URL` to use a compatible reasoning endpoint. Failed or invalid provider responses fall back to deterministic coaching.

See [Cube notation](cube-algorithms.md) for move syntax.