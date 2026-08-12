"""
CubeAI - Cube Solver

Solves a physically valid Rubik's Cube using the existing CubeAI
CubeState, Move Engine, and Cube Validator.

Architecture:

    Scanner
        |
        v
    CubeState
        |
        v
    CubeValidator
        |
        v
    CubeSolver
        |
        v
    Solution Algorithm

This module is responsible for:

    - Validating a cube before solving
    - Searching for a solution
    - Returning standard Rubik's Cube notation
    - Verifying the generated solution
    - Providing a simple CubeAI solver API

It does NOT:

    - Scan a webcam
    - Detect stickers
    - Solve colors directly from images
    - Modify the original CubeState

Move notation:

    U
    U'
    U2
    R
    R'
    R2
    F
    F'
    F2
    D
    D'
    D2
    L
    L'
    L2
    B
    B'
    B2

The solver uses the move engine from:

    ai/engine/move.py

and validation from:

    ai/engine/cubeValidator.py
"""

from __future__ import annotations

import os
import sys
from collections import deque
from dataclasses import dataclass
from typing import Iterable


# ============================================================================
# Paths
# ============================================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


# ============================================================================
# Imports
# ============================================================================

try:
    from cubeState import CubeState
except ImportError as exc:
    CubeState = None
    CUBE_STATE_IMPORT_ERROR = str(exc)
else:
    CUBE_STATE_IMPORT_ERROR = None


try:
    from move import (
        Move,
        apply_move,
        apply_moves,
        apply_algorithm,
        format_algorithm,
        parse_algorithm,
        inverse_algorithm,
    )
except ImportError as exc:
    Move = None
    apply_move = None
    apply_moves = None
    apply_algorithm = None
    format_algorithm = None
    parse_algorithm = None
    inverse_algorithm = None
    MOVE_IMPORT_ERROR = str(exc)
else:
    MOVE_IMPORT_ERROR = None


try:
    from cubeValidator import (
        CubeValidator,
        ValidationResult,
        validate_cube,
    )
except ImportError as exc:
    CubeValidator = None
    ValidationResult = None
    validate_cube = None
    VALIDATOR_IMPORT_ERROR = str(exc)
else:
    VALIDATOR_IMPORT_ERROR = None


# ============================================================================
# Constants
# ============================================================================

FACE_NAMES = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)


# Standard move order.

ALL_MOVES = (
    "U",
    "U'",
    "U2",
    "R",
    "R'",
    "R2",
    "F",
    "F'",
    "F2",
    "D",
    "D'",
    "D2",
    "L",
    "L'",
    "L2",
    "B",
    "B'",
    "B2",
)


# Opposite faces.

OPPOSITE_FACE = {
    "U": "D",
    "D": "U",
    "R": "L",
    "L": "R",
    "F": "B",
    "B": "F",
}


# ============================================================================
# Solver exceptions
# ============================================================================

class SolverError(Exception):
    """
    Base exception for solver errors.
    """


class InvalidCubeError(SolverError):
    """
    Raised when the supplied cube is physically invalid.
    """


class NoSolutionError(SolverError):
    """
    Raised when the search cannot find a solution within its limits.
    """


# ============================================================================
# Solver result
# ============================================================================

@dataclass
class SolverResult:
    """
    Result returned by CubeSolver.

    Attributes:

        solved:
            Whether the cube was solved.

        solution:
            List of Move objects.

        algorithm:
            Solution in standard notation.

        move_count:
            Number of moves.

        valid_cube:
            Whether the starting cube passed validation.

        verified:
            Whether applying the solution actually produces
            a solved cube.

        errors:
            Any errors encountered.

        nodes_searched:
            Number of states examined.
    """

    solved: bool

    solution: list[Move]

    algorithm: str

    move_count: int

    valid_cube: bool

    verified: bool

    errors: list[str]

    nodes_searched: int = 0

    def to_dict(self) -> dict:
        """
        Convert the result into a JSON-compatible dictionary.
        """

        return {
            "solved": self.solved,
            "solution": [
                str(move)
                for move in self.solution
            ],
            "algorithm": self.algorithm,
            "move_count": self.move_count,
            "valid_cube": self.valid_cube,
            "verified": self.verified,
            "errors": self.errors,
            "nodes_searched": self.nodes_searched,
        }


# ============================================================================
# Cube serialization
# ============================================================================

def _cube_key(
    cube: CubeState,
) -> tuple:
    """
    Convert a CubeState into a hashable state key.

    The complete 54-sticker state is used.

    This deliberately uses the CubeState representation instead of
    trying to maintain a second cubie representation.
    """

    values = []

    for face in FACE_NAMES:

        for row in cube.faces[face]:

            values.extend(row)

    return tuple(values)


# ============================================================================
# Solved-state helpers
# ============================================================================

def _create_solved_cube() -> CubeState:
    """
    Create the standard solved cube.

    Color scheme:

        U = white
        R = red
        F = green
        D = yellow
        L = orange
        B = blue
    """

    if CubeState is None:
        raise RuntimeError(
            "CubeState could not be imported: "
            f"{CUBE_STATE_IMPORT_ERROR}"
        )

    faces = {}

    colors = {
        "U": "white",
        "R": "red",
        "F": "green",
        "D": "yellow",
        "L": "orange",
        "B": "blue",
    }

    for face in FACE_NAMES:

        color = colors[face]

        faces[face] = [
            [color, color, color],
            [color, color, color],
            [color, color, color],
        ]

    return CubeState(faces)


def is_solved(
    cube: CubeState,
) -> bool:
    """
    Return True when every face contains one uniform color.
    """

    for face in FACE_NAMES:

        grid = cube.faces[face]

        center = grid[1][1]

        for row in grid:

            for color in row:

                if color != center:
                    return False

    return True


# ============================================================================
# Move helpers
# ============================================================================

def _move_face(
    notation: str,
) -> str:
    """
    Return the face represented by a move.
    """

    return notation[0]


def _move_modifier(
    notation: str,
) -> str:
    """
    Return the modifier represented by a move.
    """

    if len(notation) == 1:
        return ""

    return notation[1:]


def _moves_same_face(
    first: str,
    second: str,
) -> bool:
    """
    Return True if two moves operate on the same face.
    """

    return (
        _move_face(first)
        == _move_face(second)
    )


def _moves_same_axis(
    first: str,
    second: str,
) -> bool:
    """
    Return True if two moves operate on the same cube axis.

    This is useful for reducing unnecessary search branching.

    Axis groups:

        U / D
        R / L
        F / B
    """

    face_a = _move_face(first)
    face_b = _move_face(second)

    if face_a in ("U", "D"):
        return face_b in ("U", "D")

    if face_a in ("R", "L"):
        return face_b in ("R", "L")

    return face_b in ("F", "B")


# ============================================================================
# Move normalization
# ============================================================================

def _normalize_moves(
    moves: Iterable[Move],
) -> list[Move]:
    """
    Remove redundant consecutive moves.

    This uses the move engine's simplification logic indirectly by
    converting the sequence back through standard notation.

    The solver itself normally avoids generating these sequences,
    but this function is useful for the final solution.
    """

    result: list[Move] = []

    for move in moves:

        if not result:
            result.append(move)
            continue

        previous = result[-1]

        if previous.face != move.face:

            result.append(move)

            continue

        total = (
            previous.quarter_turns
            + move.quarter_turns
        ) % 4

        result.pop()

        if total == 0:
            continue

        if total == 1:
            result.append(
                Move(previous.face)
            )

        elif total == 2:
            result.append(
                Move(previous.face, "2")
            )

        else:
            result.append(
                Move(previous.face, "'")
            )

    return result


# ============================================================================
# Search node
# ============================================================================

@dataclass
class _SearchNode:
    """
    Internal search node.
    """

    cube: CubeState

    moves: tuple[str, ...]


# ============================================================================
# Cube Solver
# ============================================================================

class CubeSolver:
    """
    CubeAI Rubik's Cube solver.

    This implementation uses an iterative deepening depth-first search
    over the existing face-move engine.

    Important:

        This is intentionally a correctness-first solver.

    It is suitable for:

        - testing the CubeAI pipeline
        - validating move logic
        - solving shallow scrambles
        - integration testing with scanner.py
        - building the next solver layer

    It is NOT yet intended to compete with advanced two-phase
    Rubik's Cube solvers.

    The solver can therefore be replaced later by a faster cubie-based
    Kociemba-style solver without changing the scanner interface.
    """

    def __init__(
        self,
        max_depth: int = 7,
    ) -> None:

        if max_depth < 0:
            raise ValueError(
                "max_depth must be >= 0."
            )

        self.max_depth = max_depth

        self.nodes_searched = 0

        self._move_cache: dict[
            tuple,
            CubeState,
        ] = {}

    # ========================================================================
    # Validation
    # ========================================================================

    def validate(
        self,
        cube: CubeState,
    ):
        """
        Validate the supplied cube.
        """

        if CubeState is None:

            raise SolverError(
                "CubeState could not be imported: "
                f"{CUBE_STATE_IMPORT_ERROR}"
            )

        if validate_cube is None:

            raise SolverError(
                "CubeValidator could not be imported: "
                f"{VALIDATOR_IMPORT_ERROR}"
            )

        return validate_cube(cube)

    # ========================================================================
    # Move application
    # ========================================================================

    def _apply_notation(
        self,
        cube: CubeState,
        notation: str,
    ) -> CubeState:
        """
        Apply one notation move.
        """

        key = (
            _cube_key(cube),
            notation,
        )

        cached = self._move_cache.get(key)

        if cached is not None:
            return cached

        move = Move.parse(notation)

        result = apply_move(
            cube,
            move,
        )

        self._move_cache[key] = result

        return result

    # ========================================================================
    # Search pruning
    # ========================================================================

    @staticmethod
    def _should_prune(
        previous_move: str | None,
        current_move: str,
    ) -> bool:
        """
        Determine whether a candidate move should be skipped.

        Rules:

            1. Never perform the same face twice consecutively.

            2. Never immediately perform the exact opposite move.

            3. Canonically order opposite-face moves when they share
               an axis. This avoids searching equivalent sequences.

        These rules significantly reduce duplicate branches.
        """

        if previous_move is None:
            return False

        previous_face = _move_face(
            previous_move
        )

        current_face = _move_face(
            current_move
        )

        # Same face.

        if previous_face == current_face:
            return True

        # Opposite faces.

        if (
            OPPOSITE_FACE[previous_face]
            == current_face
        ):
            # Canonical ordering.

            return (
                current_face
                < previous_face
            )

        return False

    # ========================================================================
    # Depth-limited search
    # ========================================================================

    def _search(
        self,
        cube: CubeState,
        depth: int,
        path: list[str],
    ) -> list[str] | None:
        """
        Depth-limited DFS.

        Returns a notation sequence or None.
        """

        self.nodes_searched += 1

        if is_solved(cube):
            return list(path)

        if depth == 0:
            return None

        previous_move = (
            path[-1]
            if path
            else None
        )

        for notation in ALL_MOVES:

            if self._should_prune(
                previous_move,
                notation,
            ):
                continue

            next_cube = self._apply_notation(
                cube,
                notation,
            )

            path.append(notation)

            result = self._search(
                next_cube,
                depth - 1,
                path,
            )

            path.pop()

            if result is not None:
                return result

        return None

    # ========================================================================
    # Solve
    # ========================================================================

    def solve(
        self,
        cube: CubeState,
        *,
        verify: bool = True,
    ) -> SolverResult:
        """
        Solve a CubeState.

        Args:

            cube:
                CubeState to solve.

            verify:
                Verify the generated algorithm against the original
                cube before returning.

        Returns:

            SolverResult
        """

        self.nodes_searched = 0

        self._move_cache.clear()

        # --------------------------------------------------------------------
        # Basic type checking
        # --------------------------------------------------------------------

        if CubeState is None:

            return SolverResult(
                solved=False,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=False,
                verified=False,
                errors=[
                    "CubeState could not be imported: "
                    f"{CUBE_STATE_IMPORT_ERROR}"
                ],
            )

        if not isinstance(cube, CubeState):

            return SolverResult(
                solved=False,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=False,
                verified=False,
                errors=[
                    "cube must be a CubeState."
                ],
            )

        # --------------------------------------------------------------------
        # Validate cube
        # --------------------------------------------------------------------

        validation = self.validate(cube)

        if not validation.valid:

            return SolverResult(
                solved=False,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=False,
                verified=False,
                errors=[
                    *validation.errors
                ],
            )

        # --------------------------------------------------------------------
        # Already solved
        # --------------------------------------------------------------------

        if is_solved(cube):

            return SolverResult(
                solved=True,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=True,
                verified=True,
                errors=[],
                nodes_searched=0,
            )

        # --------------------------------------------------------------------
        # Search
        # --------------------------------------------------------------------

        found_solution: list[str] | None = None

        for depth in range(
            1,
            self.max_depth + 1,
        ):

            path: list[str] = []

            found_solution = self._search(
                cube,
                depth,
                path,
            )

            if found_solution is not None:
                break

        # --------------------------------------------------------------------
        # No solution found
        # --------------------------------------------------------------------

        if found_solution is None:

            return SolverResult(
                solved=False,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=True,
                verified=False,
                errors=[
                    "No solution found within "
                    f"depth {self.max_depth}."
                ],
                nodes_searched=self.nodes_searched,
            )

        # --------------------------------------------------------------------
        # Convert to Move objects
        # --------------------------------------------------------------------

        solution = [
            Move.parse(notation)
            for notation in found_solution
        ]

        solution = _normalize_moves(
            solution
        )

        algorithm = format_algorithm(
            solution
        )

        # --------------------------------------------------------------------
        # Verify solution
        # --------------------------------------------------------------------

        verified = False

        if verify:

            solved_cube = apply_moves(
                cube,
                solution,
            )

            verified = is_solved(
                solved_cube
            )

        else:

            verified = True

        # --------------------------------------------------------------------
        # Final result
        # --------------------------------------------------------------------

        return SolverResult(
            solved=verified,
            solution=solution,
            algorithm=algorithm,
            move_count=len(solution),
            valid_cube=True,
            verified=verified,
            errors=(
                []
                if verified
                else [
                    "Generated solution failed "
                    "verification."
                ]
            ),
            nodes_searched=self.nodes_searched,
        )


# ============================================================================
# Convenience functions
# ============================================================================

def solve_cube(
    cube: CubeState,
    max_depth: int = 7,
) -> SolverResult:
    """
    Convenience function for solving a cube.

    Example:

        result = solve_cube(cube)

        print(result.algorithm)
    """

    solver = CubeSolver(
        max_depth=max_depth
    )

    return solver.solve(
        cube
    )


def solve(
    cube: CubeState,
    max_depth: int = 7,
) -> str:
    """
    Solve a cube and return only the algorithm.

    Raises:

        SolverError
            If the cube is invalid or no solution is found.
    """

    result = solve_cube(
        cube,
        max_depth=max_depth,
    )

    if not result.valid_cube:

        raise InvalidCubeError(
            "\n".join(result.errors)
        )

    if not result.solved:

        raise NoSolutionError(
            "\n".join(result.errors)
        )

    return result.algorithm


# ============================================================================
# Apply solution
# ============================================================================

def apply_solution(
    cube: CubeState,
    solution: str | Iterable[Move],
) -> CubeState:
    """
    Apply a solution to a cube.

    Accepts either:

        "R U R'"

    or:

        [Move("R"), Move("U"), Move("R", "'")]
    """

    if isinstance(solution, str):

        return apply_algorithm(
            cube,
            solution,
        )

    return apply_moves(
        cube,
        solution,
    )


# ============================================================================
# Solver test helpers
# ============================================================================

def _test_solved_cube() -> bool:
    """
    Test solving an already solved cube.
    """

    cube = _create_solved_cube()

    result = solve_cube(
        cube
    )

    passed = (
        result.solved
        and result.algorithm == ""
        and result.move_count == 0
    )

    print(
        "Solved cube test:",
        "PASS" if passed else "FAIL",
    )

    return passed


def _test_single_move(
    notation: str,
) -> bool:
    """
    Test solving a cube scrambled by one move.
    """

    solved = _create_solved_cube()

    scrambled = apply_algorithm(
        solved,
        notation,
    )

    solver = CubeSolver(
        max_depth=2
    )

    result = solver.solve(
        scrambled
    )

    passed = (
        result.solved
        and result.verified
    )

    print(
        f"Single move test ({notation}):",
        "PASS" if passed else "FAIL",
        f"-> {result.algorithm}",
    )

    if not passed:

        for error in result.errors:
            print(
                f"  ERROR: {error}"
            )

    return passed


def _test_short_algorithm(
    algorithm: str,
    max_depth: int = 6,
) -> bool:
    """
    Test a short scramble.
    """

    solved = _create_solved_cube()

    scrambled = apply_algorithm(
        solved,
        algorithm,
    )

    solver = CubeSolver(
        max_depth=max_depth
    )

    result = solver.solve(
        scrambled
    )

    passed = (
        result.solved
        and result.verified
    )

    print(
        f"Algorithm test ({algorithm}):",
        "PASS" if passed else "FAIL",
    )

    print(
        f"  Solution: "
        f"{result.algorithm or '(already solved)'}"
    )

    print(
        f"  Moves: {result.move_count}"
    )

    print(
        f"  Nodes searched: "
        f"{result.nodes_searched}"
    )

    if result.errors:

        for error in result.errors:

            print(
                f"  ERROR: {error}"
            )

    return passed


# ============================================================================
# Main
# ============================================================================

def main() -> None:

    print(
        "CubeAI Solver"
    )

    print(
        "-------------"
    )

    print()

    # ========================================================================
    # Dependency check
    # ========================================================================

    if CubeState is None:

        print(
            "ERROR: CubeState unavailable."
        )

        print(
            CUBE_STATE_IMPORT_ERROR
        )

        return

    if Move is None:

        print(
            "ERROR: Move engine unavailable."
        )

        print(
            MOVE_IMPORT_ERROR
        )

        return

    if CubeValidator is None:

        print(
            "ERROR: CubeValidator unavailable."
        )

        print(
            VALIDATOR_IMPORT_ERROR
        )

        return

    # ========================================================================
    # Solved cube
    # ========================================================================

    cube = _create_solved_cube()

    validation = validate_cube(
        cube
    )

    print(
        "Solved cube validation:"
    )

    print(
        f"  Valid: {validation.valid}"
    )

    print()

    # ========================================================================
    # Already solved test
    # ========================================================================

    solved_test = _test_solved_cube()

    print()

    # ========================================================================
    # Single move tests
    # ========================================================================

    single_move_tests = []

    for notation in (
        "R",
        "U",
        "F",
        "D",
        "L",
        "B",
    ):

        single_move_tests.append(
            _test_single_move(
                notation
            )
        )

    print()

    # ========================================================================
    # Short scramble
    # ========================================================================

    short_scramble = (
        "R U R' U'"
    )

    short_test = _test_short_algorithm(
        short_scramble,
        max_depth=6,
    )

    print()

    # ========================================================================
    # Another scramble
    # ========================================================================

    scramble = (
        "R U R' U' F2"
    )

    integration_test = _test_short_algorithm(
        scramble,
        max_depth=7,
    )

    print()

    # ========================================================================
    # Final result
    # ========================================================================

    all_passed = (
        solved_test
        and all(single_move_tests)
        and short_test
        and integration_test
    )

    if all_passed:

        print(
            "Solver tests PASSED."
        )

    else:

        print(
            "Solver tests FAILED."
        )

    print()

    print(
        "CubeAI Solver ready."
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()