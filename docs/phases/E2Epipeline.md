# Scan-to-Solve Pipeline Status

The web scanner uploads six face photos to `POST /api/scan/image`. FastAPI runs the OpenCV face scanner, collects all six faces, builds the Python cube state, converts it to cubies, and rejects incomplete or physically invalid states. The validated state is passed to Kociemba; its returned moves are verified by the Python move engine and displayed by the TypeScript 3D player.

`tests/e2e/scan-to-playback.spec.ts` generates six face photos from a real TypeScript scramble, uploads them through the UI, and checks the returned solution in the 3D player. API tests separately exercise the real sample image scanner, face builder, solver, and WebSocket scan session.

The live camera uses browser `getUserMedia`, which requires permission and a secure context (localhost or HTTPS). The browser test uses generated image files and does not depend on physical camera hardware.

See [Features](../features.md), [API Reference](../api.md), and [Testing](../testing.md).