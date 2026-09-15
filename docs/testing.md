
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
