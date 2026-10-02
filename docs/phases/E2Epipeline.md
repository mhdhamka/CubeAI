# Scan-to-Solve Pipeline Status

The repository contains building blocks for a scan-to-solve flow: a typed API client, image-scan and solve routes, Python vision modules, cube validation, and a 3D renderer.

The complete workflow is **not connected end to end** yet:

1. The dashboard scanner does not upload images.
2. The API image-scan service validates the image but returns a placeholder solved state.
3. The API solve service returns a fixed placeholder move sequence.
4. The dashboard does not submit the returned state or solution to the API.

The TypeScript renderer can display cube state, but there is no verified image-upload-to-solution-playback flow. Treat this as an integration target, not a completed feature.

See [Features](../features.md), [API Reference](../api.md), and [Testing](../testing.md).