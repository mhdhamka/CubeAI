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
| `POST` | `/api/scan/image` | Upload an image as multipart field `file` |
| `POST` | `/api/coaching` | Request deterministic coaching |
| `POST` | `/api/profiles` | Create a profile |
| `GET`, `PUT`, `DELETE` | `/api/profiles/{profile_id}` | Read, update, or delete a profile |
| `GET` | `/api/profiles/{profile_id}/solves` | List solves (`limit`, `offset`) |
| `POST` | `/api/solves` | Create a solve record |
| `GET`, `DELETE` | `/api/solves/{solve_id}` | Read or delete a solve |
| `GET` | `/api/profiles/{profile_id}/statistics` | Profile statistics |
| `GET` | `/api/profiles/{profile_id}/statistics/improvement` | Recent trend |
| `GET` | `/api/profiles/{profile_id}/statistics/milestones` | Personal-best milestones |
| `WS` | `/api/scan/session` | Prototype scan session |

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

Validation and solve requests wrap it in `cube_state`. Solve requests may also include `max_moves`. Responses use moves with `face` (`U`, `D`, `F`, `B`, `L`, `R`) and `times` (`1`, `2`, or `3`, where `3` means a prime turn).

## Errors and limitations

Malformed request bodies receive FastAPI's `422` response. Domain errors use a structured `code`, `message`, and optional `details` object.

The route contracts exist, but two service implementations are placeholders today: `/api/solve` returns a fixed move sequence and `/api/scan/image` returns a solved state after checking that the upload is an image. The WebSocket route simulates detections. Do not treat these endpoints as production vision or solving results yet.

See [Cube notation](cube-algorithms.md) for move syntax.