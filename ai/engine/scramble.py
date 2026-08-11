
"""
CubeAI - Scramble Engine

Generates and applies valid Rubik's Cube scrambles.

A scramble is a sequence of legal face moves designed to
produce a randomized cube state.

Supported moves:

    U D R L F B

Modifiers:

    X       = clockwise quarter turn
    X'      = counter-clockwise quarter turn
    X2      = 180-degree turn

Examples:

    R U R' F2 D L' U2

This module does NOT solve the cube.

Pipeline:

    CubeState
        |
        v
    Scramble Generator
        |
        v
    Move Engine
        |
        v
    Scrambled Cube
        |
        v
    Solver
"""

from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# Imports
# ============================================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

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
        apply_moves,
        apply_scramble,
        format_algorithm,
        parse_algorithm,
    )
except ImportError as exc:
    Move = None
    apply_moves = None
    apply_scramble = None
    format_algorithm = None
    parse_algorithm = None
    MOVE_IMPORT_ERROR = str(exc)
else:
    MOVE_IMPORT_ERROR = None


# ============================================================================
# Constants
# ============================================================================

DEFAULT_SCRAMBLE_LENGTH = 20

MIN_SCRAMBLE_LENGTH = 1

MAX_SCRAMBLE_LENGTH = 100

SCRAMBLE_FACES = (
    "U",
    "D",
    "R",
    "L",
    "F",
    "B",
)

SCRAMBLE_MODIFIERS = (
    "",
    "'",
    "2",
)


# ============================================================================
# Scramble result
# ============================================================================

@dataclass(frozen=True)
class Scramble:
    """
    Represents a generated scramble.

    Attributes:

        moves:
            List of Move objects.

        notation:
            Standard Rubik's Cube notation.

        length:
            Number of moves.
    """

    moves: tuple[Move, ...]
    notation: str
    length: int

    def __str__(self) -> str:
        return self.notation

    def __len__(self) -> int:
        return self.length


# ============================================================================
# Scramble Generator
# ============================================================================

class ScrambleGenerator:
    """
    Generates legal Rubik's Cube scrambles.

    The generator prevents:

        - same-face consecutive moves
        - redundant same-axis patterns

    Example:

        R U F D L B

    is allowed.

    But:

        R R'

    is not generated.

    And patterns such as:

        R L R

    are avoided because R and L are on the same axis.
    """

    def __init__(
        self,
        seed: Optional[int] = None,
    ) -> None:

        self.random = random.Random(
            seed
        )

    # ========================================================================
    # Generate
    # ========================================================================

    def generate(
        self,
        length: int = DEFAULT_SCRAMBLE_LENGTH,
    ) -> Scramble:
        """
        Generate a random scramble.

        Parameters
        ----------

        length:
            Number of moves.

        Returns
        -------

        Scramble
            Generated scramble.
        """

        self._validate_length(
            length
        )

        moves: list[Move] = []

        while len(moves) < length:

            face = self._choose_face(
                moves
            )

            modifier = self.random.choice(
                SCRAMBLE_MODIFIERS
            )

            moves.append(
                Move(
                    face,
                    modifier,
                )
            )

        notation = format_algorithm(
            moves
        )

        return Scramble(
            moves=tuple(moves),
            notation=notation,
            length=len(moves),
        )

    # ========================================================================
    # Choose face
    # ========================================================================

    def _choose_face(
        self,
        moves: list[Move],
    ) -> str:
        """
        Choose a legal next face.

        Prevents:

            R R

        and:

            R L R

        because R/L share the same rotation axis.
        """

        previous_face = (
            moves[-1].face
            if moves
            else None
        )

        previous_axis = (
            self._face_axis(
                previous_face
            )
            if previous_face is not None
            else None
        )

        candidates = [
            face
            for face in SCRAMBLE_FACES
            if face != previous_face
            and self._face_axis(face)
            != previous_axis
        ]

        # --------------------------------------------------------------------
        # Fallback.
        #
        # This should not normally be needed, but guarantees that the
        # generator can always continue.
        # --------------------------------------------------------------------

        if not candidates:

            candidates = [
                face
                for face in SCRAMBLE_FACES
                if face != previous_face
            ]

        return self.random.choice(
            candidates
        )

    # ========================================================================
    # Face axis
    # ========================================================================

    @staticmethod
    def _face_axis(
        face: str,
    ) -> str:
        """
        Return the physical axis of a face.

            U / D -> y
            R / L -> x
            F / B -> z
        """

        if face in ("U", "D"):
            return "y"

        if face in ("R", "L"):
            return "x"

        if face in ("F", "B"):
            return "z"

        raise ValueError(
            f"Invalid scramble face: {face}"
        )

    # ========================================================================
    # Validate length
    # ========================================================================

    @staticmethod
    def _validate_length(
        length: int,
    ) -> None:

        if not isinstance(
            length,
            int,
        ):
            raise TypeError(
                "Scramble length must be an integer."
            )

        if length < MIN_SCRAMBLE_LENGTH:
            raise ValueError(
                f"Scramble length must be at least "
                f"{MIN_SCRAMBLE_LENGTH}."
            )

        if length > MAX_SCRAMBLE_LENGTH:
            raise ValueError(
                f"Scramble length cannot exceed "
                f"{MAX_SCRAMBLE_LENGTH}."
            )


# ============================================================================
# Convenience functions
# ============================================================================

def generate_scramble(
    length: int = DEFAULT_SCRAMBLE_LENGTH,
    seed: Optional[int] = None,
) -> Scramble:
    """
    Generate a random scramble.

    Example:

        scramble = generate_scramble()

        print(scramble)
    """

    generator = ScrambleGenerator(
        seed=seed
    )

    return generator.generate(
        length
    )


def generate_scramble_string(
    length: int = DEFAULT_SCRAMBLE_LENGTH,
    seed: Optional[int] = None,
) -> str:
    """
    Generate a scramble and return only its notation.
    """

    return generate_scramble(
        length=length,
        seed=seed,
    ).notation


# ============================================================================
# Scramble validation
# ============================================================================

def validate_scramble(
    scramble: str,
) -> tuple[bool, list[str]]:
    """
    Validate a scramble string.

    Returns:

        (True, [])

    for a valid scramble.

    Otherwise:

        (False, errors)
    """

    errors: list[str] = []

    if not isinstance(
        scramble,
        str,
    ):

        return (
            False,
            ["Scramble must be a string."],
        )

    scramble = scramble.strip()

    if not scramble:

        return (
            False,
            ["Scramble cannot be empty."],
        )

    if parse_algorithm is None:

        return (
            False,
            [
                "Move engine is unavailable: "
                f"{MOVE_IMPORT_ERROR}"
            ],
        )

    try:

        moves = parse_algorithm(
            scramble
        )

    except Exception as exc:

        return (
            False,
            [str(exc)],
        )

    # ------------------------------------------------------------------------
    # Check consecutive faces.
    # ------------------------------------------------------------------------

    for index in range(
        1,
        len(moves),
    ):

        previous = moves[
            index - 1
        ]

        current = moves[
            index
        ]

        if previous.face == current.face:

            errors.append(
                f"Consecutive moves use the "
                f"same face at position "
                f"{index + 1}."
            )

        if (
            ScrambleGenerator._face_axis(
                previous.face
            )
            == ScrambleGenerator._face_axis(
                current.face
            )
        ):

            errors.append(
                f"Consecutive moves use the "
                f"same axis at position "
                f"{index + 1}."
            )

    return (
        len(errors) == 0,
        errors,
    )


# ============================================================================
# Apply scramble
# ============================================================================

def scramble_cube(
    cube: CubeState,
    scramble: str,
) -> CubeState:
    """
    Apply a scramble to a CubeState.

    The original cube is not modified.
    """

    if CubeState is None:

        raise RuntimeError(
            "CubeState could not be imported: "
            f"{CUBE_STATE_IMPORT_ERROR}"
        )

    if apply_scramble is None:

        raise RuntimeError(
            "Move engine could not be imported: "
            f"{MOVE_IMPORT_ERROR}"
        )

    valid, errors = validate_scramble(
        scramble
    )

    if not valid:

        raise ValueError(
            "Invalid scramble: "
            + " ".join(errors)
        )

    return apply_scramble(
        cube,
        scramble,
    )


# ============================================================================
# Generate and scramble
# ============================================================================

def generate_scrambled_cube(
    cube: CubeState,
    length: int = DEFAULT_SCRAMBLE_LENGTH,
    seed: Optional[int] = None,
) -> tuple[Scramble, CubeState]:
    """
    Generate a scramble and apply it to a cube.

    Returns:

        (
            Scramble,
            scrambled CubeState
        )
    """

    scramble = generate_scramble(
        length=length,
        seed=seed,
    )

    scrambled_cube = scramble_cube(
        cube,
        scramble.notation,
    )

    return (
        scramble,
        scrambled_cube,
    )


# ============================================================================
# Demo helpers
# ============================================================================

def _create_solved_cube() -> CubeState:
    """
    Create a standard solved cube.

    This helper is only for demonstration/testing.
    """

    faces = {}

    for face, color in (
        ("U", "white"),
        ("R", "red"),
        ("F", "green"),
        ("D", "yellow"),
        ("L", "orange"),
        ("B", "blue"),
    ):

        faces[face] = [
            [color, color, color],
            [color, color, color],
            [color, color, color],
        ]

    return CubeState(
        faces
    )


# ============================================================================
# Main
# ============================================================================

def main() -> None:

    print(
        "CubeAI Scramble Engine"
    )

    print(
        "----------------------"
    )

    # ------------------------------------------------------------------------
    # Generate scramble
    # ------------------------------------------------------------------------

    scramble = generate_scramble(
        length=20
    )

    print()

    print(
        "Generated scramble:"
    )

    print(
        f"  {scramble}"
    )

    print(
        f"Length: {scramble.length}"
    )

    # ------------------------------------------------------------------------
    # Validate scramble
    # ------------------------------------------------------------------------

    valid, errors = validate_scramble(
        scramble.notation
    )

    print()

    print(
        "Scramble validation:"
    )

    print(
        f"  Valid: {valid}"
    )

    if errors:

        for error in errors:

            print(
                f"  - {error}"
            )

    # ------------------------------------------------------------------------
    # Deterministic generation
    # ------------------------------------------------------------------------

    seeded_a = generate_scramble(
        length=20,
        seed=42,
    )

    seeded_b = generate_scramble(
        length=20,
        seed=42,
    )

    print()

    print(
        "Seed reproducibility:"
    )

    print(
        f"  First:  {seeded_a}"
    )

    print(
        f"  Second: {seeded_b}"
    )

    print(
        "  Same:",
        seeded_a.notation
        == seeded_b.notation,
    )

    # ------------------------------------------------------------------------
    # Apply scramble to solved cube
    # ------------------------------------------------------------------------

    cube = _create_solved_cube()

    scrambled_cube = scramble_cube(
        cube,
        scramble.notation,
    )

    print()

    print(
        "Solved cube color counts:"
    )

    print(
        cube.color_counts()
    )

    print()

    print(
        "Scrambled cube color counts:"
    )

    print(
        scrambled_cube.color_counts()
    )

    # ------------------------------------------------------------------------
    # Original cube must remain solved.
    # ------------------------------------------------------------------------

    print()

    print(
        "Original cube unchanged:",
        cube.color_counts()
        == {
            "white": 9,
            "yellow": 9,
            "red": 9,
            "orange": 9,
            "green": 9,
            "blue": 9,
        },
    )

    # ------------------------------------------------------------------------
    # Empty scramble validation
    # ------------------------------------------------------------------------

    valid, errors = validate_scramble(
        ""
    )

    print()

    print(
        "Empty scramble rejected:",
        not valid,
    )

    # ------------------------------------------------------------------------
    # Invalid same-face scramble
    # ------------------------------------------------------------------------

    valid, errors = validate_scramble(
        "R R'"
    )

    print(
        "Same-face scramble rejected:",
        not valid,
    )

    # ------------------------------------------------------------------------
    # Invalid same-axis pattern
    # ------------------------------------------------------------------------

    valid, errors = validate_scramble(
        "R L"
    )

    print(
        "Same-axis scramble rejected:",
        not valid,
    )

    print()

    print(
        "Scramble engine ready!"
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()

