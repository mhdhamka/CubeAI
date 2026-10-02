# WebSocket Scan Prototype

The API exposes `WS /api/scan/session`. It sends a `scan_started` event, accepts text messages containing JSON, and responds to `frame`, `retry`, and `cancel` message types.

Current behavior is simulated: every 30 frame messages it reports a detected face with fixed sticker values, then returns a solved cube state after six faces. It does not pass camera data to the Python vision pipeline or validate a real scanned cube.

Typical event types are `scan_started`, `progress`, `face_detected`, `retry`, `completed`, `cancel`, and `error`. The TypeScript client hook is in `packages/cube-api/hooks-websocket.ts`.

Use this endpoint as a protocol prototype only. Real frame processing, validation, session persistence, and browser camera integration remain to be implemented.