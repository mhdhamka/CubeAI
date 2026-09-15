
## Overview

**CubeAI** is an experimental, full-stack platform exploring how modern software engineering, computer vision, artificial intelligence, and interactive 3D technologies can be combined to create a more intelligent Rubik's Cube experience.

Most existing cube solvers focus on a single interaction:

> **Enter cube state → Receive moves → Solve cube**

CubeAI expands this workflow into a complete learning and analysis ecosystem:

> **Scan → Validate → Understand → Solve → Visualize → Practice → Analyze → Improve**

The platform is built around a fundamental architectural principle: **the Rubik's Cube logic should not depend on the user interface, camera system, solver, or AI services**.

At the center of the project is a standalone **Cube Core Engine** responsible for representing and manipulating cube states. Other systems—including the solver, 3D renderer, computer vision scanner, and AI coach—interact with the same underlying domain model.

This approach allows CubeAI to grow from a web application into a reusable Rubik's Cube technology ecosystem.

---

## Project Vision

CubeAI aims to answer a simple question:

> **What would a modern Rubik's Cube platform look like if solving, visualization, computer vision, analytics, and AI coaching were designed as one integrated system?**

The long-term goal is to support multiple types of users:

| User                      | CubeAI Experience                                                           |
| ------------------------- | --------------------------------------------------------------------------- |
| **Beginner**           | Learn how the cube works through guided tutorials and visual explanations   |
| **Learner**            | Practice algorithms, understand notation, and receive step-by-step guidance |
| **Speedcuber**          | Track solve times, session statistics, averages, and performance trends     |
| **Physical Cube User** | Scan a real cube using a camera instead of manually entering sticker colors |
| **Advanced Solver**    | Analyze move sequences, algorithms, and alternative solving paths           |
| **Developer**          | Reuse the standalone cube engine and related packages in other applications |

---

# System Architecture

CubeAI follows a modular architecture where the core cube domain is isolated from presentation and external services.

> **Explore Further:** For detailed breakdowns of system flows, container structures, and component design, check out the [Architecture Documentation Directory](./docs/architecture/).