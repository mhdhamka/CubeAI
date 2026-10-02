# Testing

Run commands from the repository root.

## TypeScript tests

```bash
npm ci
npm run test:run
```

This runs the cube, cubie, notation, renderer, solver, and dashboard tests. To run only the dashboard tests:

```bash
npm run web:test
```

## API tests

Install Python dependencies if needed, then run:

```bash
python -m pip install -r requirements.txt -r requirements-test.txt
npm run api:test
```

The API tests cover health, validation, solve response shape, malformed requests, and SQLite persistence. They do not require PostgreSQL.

## Build and syntax checks

```bash
npm run web:build
python -m compileall apps/api ai
```

CI runs the TypeScript suite, API tests, Python compilation, and the Next.js production build.

## Browser end-to-end

Install Chromium once, then run:

```bash
npx playwright install chromium
npm run test:e2e
```

Playwright starts FastAPI with an isolated SQLite database and the web app on separate local ports. Its main flow generates face images from a legal scramble, uploads them through the UI, scans and validates the state, solves it with Python/Kociemba, and exercises the 3D playback controls.

## Current gaps

The image upload-to-playback flow is covered by Playwright. WebSocket frame processing, retry/cancel, and completion are covered with FastAPI WebSocket tests. Physical camera permission and device-specific capture still require testing on the target device/browser.