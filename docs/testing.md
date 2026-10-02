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

## Current gaps

There is no Playwright end-to-end suite yet. Browser automation was not run as part of these checks. Image-to-solution playback, real camera processing, and WebSocket vision behavior still need integration coverage once those flows use the real services.