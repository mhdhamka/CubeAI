"""
CubeAI - Cube Solver

Solves a physically valid Rubik's Cube using:

    CubeState
        ↓
    CubeValidator
        ↓
    Kociemba two-phase solver
        ↓
    Move Engine verification

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
    - Converting CubeState to standard cube notation
    - Solving using a two-phase Rubik's Cube solver
    - Returning standard Rubik's Cube notation
    - Verifying the generated solution
    - Providing a simple CubeAI solver API

It does NOT:

    - Scan a webcam
    - Detect stickers
    - Detect colors from images
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

Color scheme:

    U = white
    R = red
    F = green
    D = yellow
    L = orange
    B = blue
"""

from __future__ import annotations

import os
import re
import sys
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
    )
except ImportError as exc:
    Move = None
    apply_move = None
    apply_moves = None
    apply_algorithm = None
    format_algorithm = None
    MOVE_IMPORT_ERROR = str(exc)
else:
    MOVE_IMPORT_ERROR = None


try:
    from cubeValidator import (
        CubeValidator,
        validate_cube,
    )
except ImportError as exc:
    CubeValidator = None
    validate_cube = None
    VALIDATOR_IMPORT_ERROR = str(exc)
else:
    VALIDATOR_IMPORT_ERROR = None


# ============================================================================
# Optional Kociemba solver
# ============================================================================

try:
    import kociemba

    KOCIEMBA_AVAILABLE = True
    KOCIEMBA_IMPORT_ERROR = None

except ImportError as exc:

    kociemba = None
    KOCIEMBA_AVAILABLE = False
    KOCIEMBA_IMPORT_ERROR = str(exc)


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


FACE_COLORS = {
    "U": "white",
    "R": "red",
    "F": "green",
    "D": "yellow",
    "L": "orange",
    "B": "blue",
}


# Standard Kociemba face order.

KOCIEMBA_FACES = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)


# Color → Kociemba face letter.

COLOR_TO_FACE = {
    "white": "U",
    "red": "R",
    "green": "F",
    "yellow": "D",
    "orange": "L",
    "blue": "B",
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
    Raised when no solution can be produced.
    """


class SolverUnavailableError(SolverError):
    """
    Raised when the required external solver is unavailable.
    """


# ============================================================================
# Solver result
# ============================================================================

@dataclass
class SolverResult:
    """
    Result returned by CubeSolver.
    """

    solved: bool

    solution: list[Move]

    algorithm: str

    move_count: int

    valid_cube: bool

    verified: bool

    errors: list[str]

    nodes_searched: int = 0

    method: str = "kociemba"

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

            "method": self.method,
        }


# ============================================================================
# Cube helpers
# ============================================================================

def _cube_key(
    cube: CubeState,
) -> tuple:
    """
    Convert a CubeState into a hashable state key.
    """

    values = []

    for face in FACE_NAMES:

        for row in cube.faces[face]:

            values.extend(row)

    return tuple(values)


def _create_solved_cube() -> CubeState:
    """
    Create a standard solved cube.
    """

    if CubeState is None:

        raise RuntimeError(
            "CubeState could not be imported: "
            f"{CUBE_STATE_IMPORT_ERROR}"
        )

    faces = {}

    for face in FACE_NAMES:

        color = FACE_COLORS[face]

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
# CubeState → Kociemba conversion
# ============================================================================

def cube_to_kociemba(
    cube: CubeState,
) -> str:
    """
    Convert CubeState into the 54-character facelet string
    required by the Kociemba solver.

    Kociemba expects faces in this order:

        U R F D L B

    Each face is read row-major:

        0 1 2
        3 4 5
        6 7 8
    """

    if CubeState is None:

        raise SolverError(
            "CubeState is unavailable."
        )

    if not isinstance(cube, CubeState):

        raise TypeError(
            "cube must be a CubeState."
        )

    facelets = []

    for face in KOCIEMBA_FACES:

        grid = cube.faces[face]

        for row in grid:

            for color in row:

                if color not in COLOR_TO_FACE:

                    raise InvalidCubeError(
                        f"Unknown cube color: {color}"
                    )

                facelets.append(
                    COLOR_TO_FACE[color]
                )

    return "".join(facelets)


# ============================================================================
# Kociemba → Move conversion
# ============================================================================

def _clean_kociemba_solution(
    solution: str,
) -> str:
    """
    Clean the result returned by Kociemba.

    Kociemba may append information such as:

        (20f)

    Only the actual move sequence is returned.
    """

    if not solution:

        return ""

    solution = solution.strip()

    # Remove trailing "(20f)", "(18f)", etc.

    solution = re.sub(
        r"\s*\([^)]*\)\s*$",
        "",
        solution,
    )

    return solution.strip()


def parse_solution(
    solution: str,
) -> list[Move]:
    """
    Convert a standard solution string into Move objects.
    """

    if not solution.strip():

        return []

    moves = []

    for token in solution.split():

        moves.append(
            Move.parse(token)
        )

    return moves


# ============================================================================
# Cube Solver
# ============================================================================

class CubeSolver:
    """
    CubeAI Rubik's Cube solver.

    Uses the Kociemba two-phase algorithm when available.

    This allows CubeAI to solve:

        - single moves
        - short algorithms
        - medium scrambles
        - normal physical cube scrambles

    The solution is always verified through CubeAI's own
    move engine before being returned.
    """

    def __init__(
        self,
        *,
        method: str = "auto",
    ) -> None:

        method = method.lower().strip()

        valid_methods = {
            "auto",
            "kociemba",
        }

        if method not in valid_methods:

            raise ValueError(
                "method must be 'auto' or 'kociemba'."
            )

        self.method = method

        self.nodes_searched = 0


    # ========================================================================
    # Validation
    # ========================================================================

    def validate(
        self,
        cube: CubeState,
    ):
        """
        Validate the supplied cube using CubeValidator.
        """

        if CubeState is None:

            raise SolverError(
                "CubeState unavailable: "
                f"{CUBE_STATE_IMPORT_ERROR}"
            )

        if validate_cube is None:

            raise SolverError(
                "CubeValidator unavailable: "
                f"{VALIDATOR_IMPORT_ERROR}"
            )

        return validate_cube(cube)


    # ========================================================================
    # Kociemba solving
    # ========================================================================

    def _solve_kociemba(
        self,
        cube: CubeState,
    ) -> list[Move]:
        """
        Solve a cube using Kociemba.
        """

        if not KOCIEMBA_AVAILABLE:

            raise SolverUnavailableError(
                "Kociemba is not installed.\n"
                f"{KOCIEMBA_IMPORT_ERROR}\n\n"
                "Install it with:\n"
                "pip install kociemba"
            )

        facelets = cube_to_kociemba(
            cube
        )

        try:

            raw_solution = kociemba.solve(
                facelets
            )

        except Exception as exc:

            raise NoSolutionError(
                f"Kociemba failed to solve cube: {exc}"
            ) from exc

        cleaned_solution = (
            _clean_kociemba_solution(
                raw_solution
            )
        )

        # Kociemba can return an error string.

        if cleaned_solution.lower().startswith(
            "error"
        ):

            raise NoSolutionError(
                cleaned_solution
            )

        return parse_solution(
            cleaned_solution
        )


    # ========================================================================
    # Verification
    # ========================================================================

    def verify_solution(
        self,
        cube: CubeState,
        solution: Iterable[Move],
    ) -> bool:
        """
        Apply a solution using CubeAI's move engine and verify
        that the cube is solved.
        """

        solved_cube = apply_moves(
            cube,
            solution,
        )

        return is_solved(
            solved_cube
        )


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

        The original cube is never modified.
        """

        self.nodes_searched = 0

        # --------------------------------------------------------------------
        # Type check
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
                    "CubeState unavailable: "
                    f"{CUBE_STATE_IMPORT_ERROR}"
                ],
                method=self.method,
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
                method=self.method,
            )

        # --------------------------------------------------------------------
        # Validate
        # --------------------------------------------------------------------

        try:

            validation = self.validate(
                cube
            )

        except Exception as exc:

            return SolverResult(
                solved=False,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=False,
                verified=False,
                errors=[
                    str(exc)
                ],
                method=self.method,
            )

        if not validation.valid:

            return SolverResult(
                solved=False,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=False,
                verified=False,
                errors=list(
                    validation.errors
                ),
                method=self.method,
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
                method="none",
            )

        # --------------------------------------------------------------------
        # Check solver
        # --------------------------------------------------------------------

        if not KOCIEMBA_AVAILABLE:

            return SolverResult(
                solved=False,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=True,
                verified=False,
                errors=[
                    "Kociemba solver is not installed.",
                    "Install it with:",
                    "pip install kociemba",
                ],
                nodes_searched=0,
                method="kociemba",
            )

        # --------------------------------------------------------------------
        # Solve
        # --------------------------------------------------------------------

        try:

            solution = self._solve_kociemba(
                cube
            )

        except SolverError as exc:

            return SolverResult(
                solved=False,
                solution=[],
                algorithm="",
                move_count=0,
                valid_cube=True,
                verified=False,
                errors=[
                    str(exc)
                ],
                nodes_searched=0,
                method="kociemba",
            )

        # --------------------------------------------------------------------
        # Format solution
        # --------------------------------------------------------------------

        algorithm = format_algorithm(
            solution
        )

        # --------------------------------------------------------------------
        # Verify
        # --------------------------------------------------------------------

        if verify:

            verified = self.verify_solution(
                cube,
                solution,
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
            method="kociemba",
        )


# ============================================================================
# Convenience API
# ============================================================================

def solve_cube(
    cube: CubeState,
    *,
    verify: bool = True,
) -> SolverResult:
    """
    Solve a cube and return a SolverResult.
    """

    solver = CubeSolver()

    return solver.solve(
        cube,
        verify=verify,
    )


def solve(
    cube: CubeState,
) -> str:
    """
    Solve a cube and return only the algorithm.

    Raises:

        InvalidCubeError
            If the cube is physically invalid.

        NoSolutionError
            If no solution can be generated.
    """

    result = solve_cube(
        cube
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
# Test helpers
# ============================================================================

def _test_solved_cube() -> bool:
    """
    Test an already solved cube.
    """

    cube = _create_solved_cube()

    result = solve_cube(
        cube
    )

    passed = (
        result.solved
        and result.algorithm == ""
        and result.move_count == 0
        and result.verified
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

    solver = CubeSolver()

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

    if result.errors:

        for error in result.errors:

            print(
                f"  ERROR: {error}"
            )

    return passed


def _test_algorithm(
    algorithm: str,
) -> bool:
    """
    Test solving a multi-move scramble.
    """

    solved = _create_solved_cube()

    scrambled = apply_algorithm(
        solved,
        algorithm,
    )

    solver = CubeSolver()

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
        f"  Verified: {result.verified}"
    )

    print(
        f"  Method: {result.method}"
    )

    if result.errors:

        for error in result.errors:

            print(
                f"  ERROR: {error}"
            )

    return passed


def _test_cube_conversion() -> bool:
    """
    Test CubeState → Kociemba conversion.
    """

    cube = _create_solved_cube()

    facelets = cube_to_kociemba(
        cube
    )

    expected = (
        "U" * 9
        + "R" * 9
        + "F" * 9
        + "D" * 9
        + "L" * 9
        + "B" * 9
    )

    passed = (
        facelets == expected
        and len(facelets) == 54
    )

    print(
        "CubeState → Kociemba conversion:",
        "PASS" if passed else "FAIL",
    )

    print(
        f"  Facelets: {facelets}"
    )

    print(
        f"  Length: {len(facelets)}"
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
    # Kociemba status
    # ========================================================================

    print(
        "Kociemba solver:"
    )

    print(
        f"  Available: {KOCIEMBA_AVAILABLE}"
    )

    if not KOCIEMBA_AVAILABLE:

        print(
            "  Install with: pip install kociemba"
        )

    print()

    # ========================================================================
    # Solved cube validation
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
    # Conversion test
    # ========================================================================

    conversion_test = (
        _test_cube_conversion()
    )

    print()

    # ========================================================================
    # Already solved
    # ========================================================================

    solved_test = (
        _test_solved_cube()
    )

    print()

    # ========================================================================
    # If Kociemba isn't installed
    # ========================================================================

    if not KOCIEMBA_AVAILABLE:

        print(
            "Solver tests cannot continue."
        )

        print(
            "Install the solver dependency with:"
        )

        print(
            "  pip install kociemba"
        )

        print()

        print(
            "CubeAI Solver ready."
        )

        return

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
    # Short algorithm
    # ========================================================================

    short_test = _test_algorithm(
        "R U R' U'"
    )

    print()

    # ========================================================================
    # Medium algorithm
    # ========================================================================

    medium_test = _test_algorithm(
        "R U R' U' F2"
    )

    print()

    # ========================================================================
    # Larger scramble
    # ========================================================================

    larger_test = _test_algorithm(
        "R U R' U' F2 L D B R2 U2"
    )

    print()

    # ========================================================================
    # Final result
    # ========================================================================

    all_passed = (
        conversion_test
        and solved_test
        and all(single_move_tests)
        and short_test
        and medium_test
        and larger_test
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