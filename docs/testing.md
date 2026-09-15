# Testing Strategy

Because cube manipulation logic is highly state-dependent, testing is a critical part of the project.

The Cube Core Engine should be tested independently from the UI.

### Core Test Examples

* A move followed by its inverse restores the original state.
* Four quarter turns restore the original state.
* Scrambled cubes contain valid piece configurations.
* Invalid sticker configurations are rejected.
* Move sequences produce deterministic results.
* Serialization preserves the cube state.

Example concept:

```text
R + R' = Solved State

R R R R = Solved State

Algorithm + Inverse Algorithm = Original State

```

Testing categories include:

* **Unit Tests** — Individual moves, parsers, validators, and utilities
* **Integration Tests** — Communication between packages and services
* **End-to-End Tests** — Complete user workflows
* **Visual Testing** — 3D rendering and animation behavior
* **Validation Testing** — Detection of impossible cube states

---

### Test Structure & Fixtures

The test suite is organized to validate everything from base components to computer vision pipelines using real sample assets:

```text
tests/
├── cube.test.ts          # Core state and move validation tests
├── cubie.test.ts         # Individual piece rotation logic
├── notation.test.ts      # Move notation parser tests
├── renderer.test.ts      # 3D abstraction and rendering tests
└── solver.test.ts        # Solving algorithm integration tests

# Vision & Scanner Test Assets
├── cube.jpg              # Sample physical cube photo for scanner tests
└── cube-color.jpg        # Sample sticker color-detection fixture

```

---

> **Quick Navigation:** Explore the test suite in [tests](../tests/) or view sample assets in [test-images](../test-images/)