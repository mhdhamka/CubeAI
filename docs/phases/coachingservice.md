# Coaching Service

The API exposes deterministic coaching at `POST /api/coaching`. It accepts a cube state, a list of solution moves, and an optional focus (`cross`, `f2l`, `oll`, `pll`, or `overall`). It returns an explanation, key points, suggested algorithms, and a difficulty label.

The service currently generates rule-based guidance. It does not call an external reasoning model or persist coaching history as part of the request flow.

Related code:

- `apps/api/routes/coaching.py`
- `apps/api/services/coaching.py`
- `packages/cube-api/hooks.ts`

See [API Reference](../api.md) for the route list.