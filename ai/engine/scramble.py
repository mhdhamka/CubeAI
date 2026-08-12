"""
CubeAI - Scramble Engine

Generates, validates, and applies legal Rubik's Cube scrambles.

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
    Scramble Validator
        |
        v
    Move Engine
        |
        v
    CubeValidator
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
        apply_scramble,
        format_algorithm,
        parse_algorithm,
    )
except ImportError as exc:
    Move = None
    apply_scramble = None
    format_algorithm = None
    parse_algorithm = None
    MOVE_IMPORT_ERROR = str(exc)
else:
    MOVE_IMPORT_ERROR = None


# CubeValidator is intentionally optional so that scramble.py
# can still be imported independently during development.
try:
    from cubeValidator import (
        CubeValidator,
    )
except ImportError as exc:
    CubeValidator = None
    CUBE_VALIDATOR_IMPORT_ERROR = str(exc)
else:
    CUBE_VALIDATOR_IMPORT_ERROR = None


# ============================================================================
# Constants
# ============================================================================

DEFAULT_SCRAMBLE_LENGTH = 20

MIN_SCRAMBLE_LENGTH = 1

MAX_SCRAMBLE_LENGTH = 100

DEFAULT_VALIDATION_SAMPLES = 100

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
            Tuple of Move objects.

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

        - consecutive moves on the same face
        - consecutive moves on the same axis

    Examples:

        Allowed:

            R U F D L B

        Rejected:

            R R'

        Rejected:

            R L

        Rejected:

            R L R

    Preventing consecutive same-axis moves produces cleaner,
    more standard-style scrambles.
    """

    def __init__(
        self,
        seed: Optional[int] = None,
    ) -> None:

        self.random = random.Random(seed)

    # ========================================================================
    # Generate
    # ========================================================================

    def generate(
        self,
        length: int = DEFAULT_SCRAMBLE_LENGTH,
    ) -> Scramble:
        """
        Generate a random legal scramble.

        Parameters
        ----------
        length:
            Number of moves.

        Returns
        -------
        Scramble
            Generated scramble.
        """

        self._validate_length(length)

        if Move is None:
            raise RuntimeError(
                "Move engine could not be imported: "
                f"{MOVE_IMPORT_ERROR}"
            )

        if format_algorithm is None:
            raise RuntimeError(
                "Move formatter is unavailable."
            )

        moves: list[Move] = []

        while len(moves) < length:

            face = self._choose_face(moves)

            modifier = self.random.choice(
                SCRAMBLE_MODIFIERS
            )

            moves.append(
                Move(
                    face,
                    modifier,
                )
            )

        notation = format_algorithm(moves)

        scramble = Scramble(
            moves=tuple(moves),
            notation=notation,
            length=len(moves),
        )

        # Generated scrambles should always pass our own
        # structural validation.
        valid, errors = validate_scramble(
            scramble.notation
        )

        if not valid:
            raise RuntimeError(
                "Scramble generator produced an invalid "
                f"scramble: {' '.join(errors)}"
            )

        return scramble

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

            R L

        because R/L share the same axis.
        """

        previous_face = (
            moves[-1].face
            if moves
            else None
        )

        previous_axis = (
            self._face_axis(previous_face)
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

        if not candidates:

            # This should never happen with the six standard
            # Rubik's Cube faces, but guarantees progress.
            candidates = [
                face
                for face in SCRAMBLE_FACES
                if face != previous_face
            ]

        return self.random.choice(candidates)

    # ========================================================================
    # Face axis
    # ========================================================================

    @staticmethod
    def _face_axis(
        face: str,
    ) -> str:
        """
        Return the physical rotation axis of a face.

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
        """
        Validate scramble length.
        """

        if not isinstance(length, int):
            raise TypeError(
                "Scramble length must be an integer."
            )

        if isinstance(length, bool):
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

    return generator.generate(length)


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

    Checks:

        1. Input is a string.
        2. Input is not empty.
        3. All moves can be parsed by move.py.
        4. No consecutive moves use the same face.
        5. No consecutive moves use the same axis.
        6. Every move uses a supported scramble face.
        7. Every move uses a supported modifier.

    Returns:

        (True, [])

    for a valid scramble.

    Otherwise:

        (False, errors)
    """

    errors: list[str] = []

    if not isinstance(scramble, str):
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
        moves = parse_algorithm(scramble)

    except Exception as exc:
        return (
            False,
            [str(exc)],
        )

    if not moves:
        return (
            False,
            ["Scramble contains no moves."],
        )

    # ========================================================================
    # Validate individual moves
    # ========================================================================

    for index, move in enumerate(moves):

        if move.face not in SCRAMBLE_FACES:
            errors.append(
                f"Invalid face '{move.face}' "
                f"at position {index + 1}."
            )

        if move.modifier not in SCRAMBLE_MODIFIERS:
            errors.append(
                f"Invalid modifier '{move.modifier}' "
                f"at position {index + 1}."
            )

    # ========================================================================
    # Validate consecutive moves
    # ========================================================================

    for index in range(1, len(moves)):

        previous = moves[index - 1]
        current = moves[index]

        if previous.face == current.face:
            errors.append(
                "Consecutive moves use the same face "
                f"at positions {index} and {index + 1}."
            )

        previous_axis = (
            ScrambleGenerator._face_axis(
                previous.face
            )
        )

        current_axis = (
            ScrambleGenerator._face_axis(
                current.face
            )
        )

        if previous_axis == current_axis:
            errors.append(
                "Consecutive moves use the same axis "
                f"at positions {index} and {index + 1}."
            )

    return (
        len(errors) == 0,
        errors,
    )


def is_scramble_valid(
    scramble: str,
) -> bool:
    """
    Return True if a scramble string is valid.
    """

    valid, _ = validate_scramble(
        scramble
    )

    return valid


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
# Validate scrambled cube
# ============================================================================

def validate_scrambled_cube(
    cube: CubeState,
    scramble: str,
) -> tuple[bool, list[str]]:
    """
    Apply a scramble and validate the resulting CubeState.

    This performs the complete pipeline:

        scramble
            |
            v
        Move Engine
            |
            v
        CubeState
            |
            v
        CubeValidator

    Returns:

        (True, [])

    when the resulting cube is physically valid.
    """

    if CubeValidator is None:
        return (
            False,
            [
                "CubeValidator could not be imported: "
                f"{CUBE_VALIDATOR_IMPORT_ERROR}"
            ],
        )

    try:
        scrambled_cube = scramble_cube(
            cube,
            scramble,
        )

    except Exception as exc:
        return (
            False,
            [
                f"Failed to apply scramble: {exc}"
            ],
        )

    validator = CubeValidator()

    result = validator.validate(
        scrambled_cube
    )

    if result.valid:
        return (
            True,
            [],
        )

    return (
        False,
        result.errors,
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


def generate_valid_scrambled_cube(
    cube: CubeState,
    length: int = DEFAULT_SCRAMBLE_LENGTH,
    seed: Optional[int] = None,
) -> tuple[Scramble, CubeState]:
    """
    Generate a scramble, apply it, and verify the resulting
    cube using CubeValidator.

    Raises RuntimeError if the generated state is invalid.
    """

    scramble, scrambled_cube = (
        generate_scrambled_cube(
            cube,
            length=length,
            seed=seed,
        )
    )

    if CubeValidator is None:
        raise RuntimeError(
            "CubeValidator could not be imported: "
            f"{CUBE_VALIDATOR_IMPORT_ERROR}"
        )

    validator = CubeValidator()

    result = validator.validate(
        scrambled_cube
    )

    if not result.valid:
        raise RuntimeError(
            "Generated scramble produced an invalid "
            f"cube state.\n"
            f"Scramble: {scramble.notation}\n"
            "Errors:\n"
            + "\n".join(
                f"  - {error}"
                for error in result.errors
            )
        )

    return (
        scramble,
        scrambled_cube,
    )


# ============================================================================
# Batch validation
# ============================================================================

def test_random_scrambles(
    cube: CubeState,
    samples: int = DEFAULT_VALIDATION_SAMPLES,
    length: int = DEFAULT_SCRAMBLE_LENGTH,
    seed: Optional[int] = None,
) -> tuple[int, int, list[str]]:
    """
    Generate and validate multiple random scrambles.

    This is an integration test between:

        ScrambleGenerator
              |
              v
          move.py
              |
              v
        CubeValidator

    Returns:

        passed,
        failed,
        failure_messages
    """

    if not isinstance(samples, int):
        raise TypeError(
            "samples must be an integer."
        )

    if samples < 1:
        raise ValueError(
            "samples must be at least 1."
        )

    ScrambleGenerator._validate_length(
        length
    )

    generator = ScrambleGenerator(
        seed=seed
    )

    validator = None

    if CubeValidator is not None:
        validator = CubeValidator()

    passed = 0
    failed = 0
    failures: list[str] = []

    for index in range(samples):

        scramble = generator.generate(
            length
        )

        try:
            scrambled_cube = scramble_cube(
                cube,
                scramble.notation,
            )

        except Exception as exc:

            failed += 1

            failures.append(
                f"Test {index + 1}: "
                f"Move engine failed for "
                f"'{scramble.notation}': {exc}"
            )

            continue

        if validator is None:

            failed += 1

            failures.append(
                "CubeValidator unavailable: "
                f"{CUBE_VALIDATOR_IMPORT_ERROR}"
            )

            continue

        result = validator.validate(
            scrambled_cube
        )

        if result.valid:
            passed += 1

        else:
            failed += 1

            failures.append(
                f"Test {index + 1}: "
                f"Invalid cube from scramble "
                f"'{scramble.notation}': "
                + " | ".join(
                    result.errors
                )
            )

    return (
        passed,
        failed,
        failures,
    )


# ============================================================================
# Demo helpers
# ============================================================================

def _create_solved_cube() -> CubeState:
    """
    Create a standard solved cube.

    This helper is only for demonstration/testing.
    """

    if CubeState is None:
        raise RuntimeError(
            "CubeState could not be imported: "
            f"{CUBE_STATE_IMPORT_ERROR}"
        )

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

    # ========================================================================
    # Generate scramble
    # ========================================================================

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
        f"  Length: {scramble.length}"
    )

    # ========================================================================
    # Validate scramble
    # ========================================================================

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

    # ========================================================================
    # Deterministic generation
    # ========================================================================

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
        f"  Same:   "
        f"{seeded_a.notation == seeded_b.notation}"
    )

    # ========================================================================
    # Apply scramble
    # ========================================================================

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
        f"  {cube.color_counts()}"
    )

    print()

    print(
        "Scrambled cube color counts:"
    )

    print(
        f"  {scrambled_cube.color_counts()}"
    )

    # ========================================================================
    # Validate scrambled cube with CubeValidator
    # ========================================================================

    print()

    print(
        "CubeValidator integration:"
    )

    if CubeValidator is None:

        print(
            "  Validator unavailable:"
        )

        print(
            f"  {CUBE_VALIDATOR_IMPORT_ERROR}"
        )

    else:

        validator = CubeValidator()

        validation_result = validator.validate(
            scrambled_cube
        )

        print(
            f"  Valid: "
            f"{validation_result.valid}"
        )

        print(
            f"  Corner orientation sum: "
            f"{validation_result.corner_orientation_sum}"
        )

        print(
            f"  Edge orientation sum: "
            f"{validation_result.edge_orientation_sum}"
        )

        print(
            f"  Corner parity: "
            f"{validation_result.corner_permutation_parity}"
        )

        print(
            f"  Edge parity: "
            f"{validation_result.edge_permutation_parity}"
        )

        if validation_result.errors:

            print()

            print(
                "  Errors:"
            )

            for error in validation_result.errors:

                print(
                    f"    - {error}"
                )

    # ========================================================================
    # Original cube must remain unchanged
    # ========================================================================

    print()

    expected_solved_counts = {
        "white": 9,
        "yellow": 9,
        "red": 9,
        "orange": 9,
        "green": 9,
        "blue": 9,
    }

    print(
        "Original cube unchanged:",
        cube.color_counts()
        == expected_solved_counts,
    )

    # ========================================================================
    # Invalid scramble tests
    # ========================================================================

    valid, errors = validate_scramble(
        ""
    )

    print()

    print(
        "Empty scramble rejected:",
        not valid,
    )

    valid, errors = validate_scramble(
        "R R'"
    )

    print(
        "Same-face scramble rejected:",
        not valid,
    )

    valid, errors = validate_scramble(
        "R L"
    )

    print(
        "Same-axis scramble rejected:",
        not valid,
    )

    valid, errors = validate_scramble(
        "R X"
    )

    print(
        "Invalid-face scramble rejected:",
        not valid,
    )

    # ========================================================================
    # Random integration test
    # ========================================================================

    print()

    print(
        "Random scramble integration test:"
    )

    passed, failed, failures = (
        test_random_scrambles(
            cube,
            samples=100,
            length=20,
            seed=42,
        )
    )

    print(
        f"  Samples: 100"
    )

    print(
        f"  Passed:  {passed}"
    )

    print(
        f"  Failed:  {failed}"
    )

    if failures:

        print()

        print(
            "  Failures:"
        )

        for failure in failures[:10]:

            print(
                f"    - {failure}"
            )

        if len(failures) > 10:

            print(
                f"    ... and "
                f"{len(failures) - 10} more."
            )

    print()

    if failed == 0:

        print(
            "100/100 scramble validation tests: PASS"
        )

    else:

        print(
            "Scramble integration tests: FAIL"
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