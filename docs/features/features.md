
# Key Features

## Standalone Cube Core Engine

The Cube Core Engine is the foundation of CubeAI.

Rather than embedding Rubik's Cube logic directly inside React components or API endpoints, cube operations are implemented as a standalone domain package.

### Responsibilities

* Cube state representation
* Face rotations
* Standard move execution
* Whole-cube rotations
* Move inversion
* Move sequences and algorithms
* Scramble generation
* Cube state validation
* Serialization and deserialization
* Integration with solver and renderer packages

### Supported Move Concepts

The engine is designed to support standard Singmaster notation:

```text
R   Right clockwise
R'  Right counter-clockwise
R2  Right double turn

U   Up clockwise
D   Down clockwise
L   Left clockwise
F   Front clockwise
B   Back clockwise
```

Future support can include:

* Wide moves (`Rw`, `Uw`, etc.)
* Slice moves (`M`, `E`, `S`)
* Cube rotations (`x`, `y`, `z`)
* Algorithm macros
* Custom notation formats

### Why a Standalone Core?

A dedicated core makes it possible for the same cube state to be used by:

* The web application
* The 3D renderer
* The solver
* Computer vision services
* AI coaching services
* Automated tests
* Future mobile applications

The cube should behave identically regardless of where it is displayed.

---

## Intelligent Solver System

CubeAI's solver subsystem is responsible for transforming a valid scrambled cube state into a sequence of legal moves.

The architecture is designed to support multiple solving strategies rather than permanently coupling the platform to one algorithm.

### Planned Solver Capabilities

* Kociemba Two-Phase solving
* Search-based solving using IDA*
* Move sequence optimization
* Alternative solution comparison
* Solution metrics
* Move count analysis
* Execution-friendly solutions

### Solver Pipeline

```text
CubeState
    │
    ▼
State Validation
    │
    ▼
Solver Selection
    │
    ├── Fast Solver
    ├── Optimal / Search Solver
    └── Educational Solver
    │
    ▼
Raw Move Sequence
    │
    ▼
Move Optimization
    │
    ▼
Solution Result
```

A solver result can contain more than just moves:

```typescript
interface SolutionResult {
  moves: string[];
  moveCount: number;
  executionTime: number;
  method: string;
  explanation?: string;
}
```

This allows the AI coaching layer and analytics system to understand the context behind a solution.

---

## Interactive 3D Cube Simulation

CubeAI uses a 3D visualization layer to make cube states and algorithms easier to understand.

Rather than showing a plain text sequence such as:

```text
R U R' U'
```

the platform can visually demonstrate each move on an interactive cube.

### Planned Capabilities

* Interactive 3D Rubik's Cube
* Mouse and touch controls
* Individual face rotations
* Smooth move animations
* Step-by-step solution playback
* Play, pause, next, and previous controls
* Algorithm demonstrations
* Camera rotation
* Scramble visualization

### Technology

The rendering layer is designed around:

* Three.js
* React Three Fiber
* TypeScript
* Shared Cube Core state

The renderer should **consume cube states rather than own cube logic**, ensuring visual animation never becomes the source of truth for the actual cube state.

---

## Computer Vision Cube Scanner

The computer vision subsystem aims to allow users to scan a physical Rubik's Cube using a camera.

The system will process captured faces and reconstruct a valid digital cube state.

### Vision Pipeline

```text
Camera Stream
      │
      ▼
Frame Processing
      │
      ▼
Cube / Face Detection
      │
      ▼
Sticker Grid Detection
      │
      ▼
Color Sampling
      │
      ▼
Color Classification
      │
      ▼
Face Reconstruction
      │
      ▼
Cube State Validation
```

### Planned Technologies

* OpenCV
* NumPy
* Custom color classification
* Geometric contour detection
* Optional MediaPipe-based vision utilities

### Key Challenges

Computer vision introduces challenges that are not present when manually entering a cube state:

* Different lighting conditions
* Sticker reflections
* Camera white balance
* Cube orientation
* Similar colors
* Shadows and occlusion
* Invalid or physically impossible states

For this reason, the scanner is treated as an input system—not the authority on cube correctness. Every reconstructed state should pass through the **Cube Core validation layer** before reaching the solver.

---

## AI Coach & Learning System

The AI Coach is intended to differentiate CubeAI from a traditional solver.

Instead of only answering:

> "Do these moves."

The system aims to explain:

> "Why are these moves being performed, what is happening to the cube, and what should you learn from this step?"

### Planned Learning Areas

#### 🟢 Beginner Learning

* Cube fundamentals
* Understanding faces and pieces
* Move notation
* First layer
* Second layer
* Beginner last-layer techniques

#### 🔵 Intermediate Learning

* CFOP fundamentals
* Cross planning
* F2L pair recognition
* Efficient finger tricks
* Lookahead concepts

#### 🟣 Advanced Training

* OLL recognition
* PLL recognition
* Algorithm optimization
* Execution efficiency
* Case recognition training

### AI Coaching Experience

```text
User Action
    │
    ▼
Cube Context + Learning Goal
    │
    ▼
AI Coaching Engine
    │
    ├── Explain
    ├── Demonstrate
    ├── Ask Questions
    ├── Identify Mistakes
    └── Recommend Practice
    │
    ▼
Personalized Feedback
```

The AI should ideally be grounded in structured cube data, algorithms, and validated cube states rather than relying solely on unrestricted text generation.

---

## Speedcubing Timer & Analytics

CubeAI will include a telemetry and statistics system for tracking solving performance.

### Planned Statistics

* Individual solve times
* Session history
* Personal best
* Mean and median
* Average of 5 (Ao5)
* Average of 12 (Ao12)
* Average of 100 (Ao100)
* Historical performance trends
* Session consistency
* Progress over time

Example session data:

```text
Session #12

Solve 1   12.42s
Solve 2   11.89s
Solve 3   13.01s
Solve 4   11.45s
Solve 5   12.10s

Ao5       12.14s
Best      11.45s
```

Future analytics may identify patterns such as:

* Performance improvements
* Consistency problems
* Training plateaus
* Algorithm-specific weaknesses

---
