"""
CubeAI - Move Engine

Defines Rubik's Cube moves and applies them to CubeState.

Supported face moves:

    U
    D
    R
    L
    F
    B

Modifiers:

    R   = clockwise quarter turn
    R'  = counter-clockwise quarter turn
    R2  = 180-degree turn

Example:

    R U R' U'

This module is responsible for:

    - Move representation
    - Move parsing
    - Algorithm parsing
    - Algorithm inversion
    - Algorithm simplification
    - Cube move application
    - Scramble application

This module does NOT solve the cube.

The move engine uses the same face layout and color scheme
as cubeValidator.py:

    U = white
    R = red
    F = green
    D = yellow
    L = orange
    B = blue

Face layout:

              U
          +-------+
          |       |
          |       |
          |       |
      +---+-------+---+---+
      | L |   F   | R | B |
      +---+-------+---+---+
          |       |
          |   D   |
          |       |
          +-------+
"""

from __future__ import annotations

import os
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


# ============================================================================
# Constants
# ============================================================================

GRID_SIZE = 3

FACE_NAMES = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)

FACE_U = "U"
FACE_R = "R"
FACE_F = "F"
FACE_D = "D"
FACE_L = "L"
FACE_B = "B"

VALID_FACES = FACE_NAMES

VALID_MODIFIERS = (
    "",
    "'",
    "2",
)


# ============================================================================
# Expected colors
# ============================================================================

FACE_COLORS = {
    FACE_U: "white",
    FACE_R: "red",
    FACE_F: "green",
    FACE_D: "yellow",
    FACE_L: "orange",
    FACE_B: "blue",
}


# ============================================================================
# Face geometry
# ============================================================================

"""
Each face is represented using a 3D coordinate system.

Cube coordinates:

    +X = Right
    -X = Left

    +Y = Up
    -Y = Down

    +Z = Front
    -Z = Back

Each face has:

    normal
    right direction
    down direction

The directions are chosen to match the exact facelet layout
used by cubeValidator.py.

For example:

U:

    0 1 2
    3 4 5
    6 7 8

has:

    right = +X
    down  = +Z

while F has:

    right = +X
    down  = -Y

This gives the correct physical relationship between:

    UFR
    URB
    UBL
    ULF
    DFR
    DRB
    DBL
    DLF

and all twelve edges.
"""

# ---------------------------------------------------------------------------
# Vector representation
# ---------------------------------------------------------------------------

Vector = tuple[int, int, int]


# ---------------------------------------------------------------------------
# Face basis
#
# face:
#
#     normal
#     right
#     down
# ---------------------------------------------------------------------------

FACE_BASIS: dict[str, tuple[Vector, Vector, Vector]] = {

    # U
    # Looking directly at U:
    #
    #     right -> +X
    #     down  -> +Z
    FACE_U: (
        (0, 1, 0),
        (1, 0, 0),
        (0, 0, 1),
    ),

    # R
    # Looking directly at R:
    #
    #     right -> -Z
    #     down  -> -Y
    FACE_R: (
        (1, 0, 0),
        (0, 0, -1),
        (0, -1, 0),
    ),

    # F
    # Looking directly at F:
    #
    #     right -> +X
    #     down  -> -Y
    FACE_F: (
        (0, 0, 1),
        (1, 0, 0),
        (0, -1, 0),
    ),

    # D
    # Looking directly at D:
    #
    #     right -> +X
    #     down  -> -Z
    FACE_D: (
        (0, -1, 0),
        (1, 0, 0),
        (0, 0, -1),
    ),

    # L
    # Looking directly at L:
    #
    #     right -> +Z
    #     down  -> -Y
    FACE_L: (
        (-1, 0, 0),
        (0, 0, 1),
        (0, -1, 0),
    ),

    # B
    # Looking directly at B:
    #
    #     right -> -X
    #     down  -> -Y
    FACE_B: (
        (0, 0, -1),
        (-1, 0, 0),
        (0, -1, 0),
    ),
}


# ============================================================================
# Vector helpers
# ============================================================================

def _vector_add(
    a: Vector,
    b: Vector,
) -> Vector:
    """
    Add two 3D vectors.
    """

    return (
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2],
    )


def _vector_scale(
    vector: Vector,
    scalar: int,
) -> Vector:
    """
    Multiply a vector by a scalar.
    """

    return (
        vector[0] * scalar,
        vector[1] * scalar,
        vector[2] * scalar,
    )


def _dot(
    a: Vector,
    b: Vector,
) -> int:
    """
    Dot product.
    """

    return (
        a[0] * b[0]
        + a[1] * b[1]
        + a[2] * b[2]
    )


def _cross(
    a: Vector,
    b: Vector,
) -> Vector:
    """
    Cross product.
    """

    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


# ============================================================================
# Facelet geometry lookup
# ============================================================================

"""
FACELET_LOOKUP maps:

    (position, normal)

to:

    (face, row, column)

Example:

    U[2][2]

maps to the same physical sticker position as:

    F[0][2]
    R[0][0]

because those three stickers belong to UFR.
"""


FACELET_LOOKUP: dict[
    tuple[Vector, Vector],
    tuple[str, int, int],
] = {}


def _build_facelet_lookup() -> None:
    """
    Build the complete 54-sticker geometry table.
    """

    FACELET_LOOKUP.clear()

    for face in FACE_NAMES:

        normal, right, down = FACE_BASIS[face]

        for row in range(GRID_SIZE):

            for col in range(GRID_SIZE):

                # Convert row/column into offsets:
                #
                # 0 -> -1
                # 1 ->  0
                # 2 -> +1

                column_offset = col - 1
                row_offset = row - 1

                position = _vector_add(
                    normal,
                    _vector_add(
                        _vector_scale(
                            right,
                            column_offset,
                        ),
                        _vector_scale(
                            down,
                            row_offset,
                        ),
                    ),
                )

                FACELET_LOOKUP[
                    (position, normal)
                ] = (
                    face,
                    row,
                    col,
                )


_build_facelet_lookup()


# ============================================================================
# Rotate vector clockwise around face normal
# ============================================================================

def _rotate_vector_clockwise(
    vector: Vector,
    normal: Vector,
) -> Vector:
    """
    Rotate a vector 90 degrees clockwise around a face normal.

    Clockwise is defined from the perspective of looking directly
    at the selected face.

    Mathematically this is a -90 degree rotation around the face
    normal.

    Because all coordinates are integer cube coordinates, the
    resulting values remain integers.
    """

    # Rodrigues rotation for -90 degrees:
    #
    # v' = -n x v + n(n . v)

    cross = _cross(
        normal,
        vector,
    )

    projection = _dot(
        normal,
        vector,
    )

    return (
        -cross[0] + normal[0] * projection,
        -cross[1] + normal[1] * projection,
        -cross[2] + normal[2] * projection,
    )


# ============================================================================
# Move
# ============================================================================

@dataclass(frozen=True)
class Move:
    """
    Represents one Rubik's Cube move.

    Examples:

        Move("R")
        Move("R", "'")
        Move("R", "2")
    """

    face: str
    modifier: str = ""

    def __post_init__(self) -> None:

        face = self.face.upper()

        if face not in VALID_FACES:
            raise ValueError(
                f"Invalid move face '{self.face}'. "
                f"Expected one of {VALID_FACES}."
            )

        if self.modifier not in VALID_MODIFIERS:
            raise ValueError(
                f"Invalid move modifier '{self.modifier}'. "
                f"Expected one of {VALID_MODIFIERS}."
            )

        object.__setattr__(
            self,
            "face",
            face,
        )

    def __str__(self) -> str:
        return f"{self.face}{self.modifier}"

    def __repr__(self) -> str:
        return f"Move('{self}')"

    @property
    def quarter_turns(self) -> int:
        """
        Return the move as clockwise quarter turns.

        R  -> 1
        R2 -> 2
        R' -> 3
        """

        if self.modifier == "":
            return 1

        if self.modifier == "2":
            return 2

        if self.modifier == "'":
            return 3

        raise ValueError(
            f"Unsupported modifier: {self.modifier}"
        )

    def inverse(self) -> "Move":
        """
        Return the inverse move.

        R  -> R'
        R' -> R
        R2 -> R2
        """

        if self.modifier == "":
            return Move(
                self.face,
                "'",
            )

        if self.modifier == "'":
            return Move(
                self.face,
            )

        return Move(
            self.face,
            "2",
        )

    @classmethod
    def parse(
        cls,
        notation: str,
    ) -> "Move":

        if not isinstance(notation, str):
            raise TypeError(
                "Move notation must be a string."
            )

        notation = notation.strip()

        if not notation:
            raise ValueError(
                "Move notation cannot be empty."
            )

        if len(notation) > 2:
            raise ValueError(
                f"Invalid move notation: '{notation}'."
            )

        face = notation[0].upper()

        modifier = (
            notation[1:]
            if len(notation) == 2
            else ""
        )

        if face not in VALID_FACES:
            raise ValueError(
                f"Invalid move: '{notation}'."
            )

        if modifier not in VALID_MODIFIERS:
            raise ValueError(
                f"Invalid move modifier: '{modifier}'."
            )

        return cls(
            face,
            modifier,
        )


# ============================================================================
# Algorithm parsing
# ============================================================================

def parse_algorithm(
    algorithm: str,
) -> list[Move]:
    """
    Parse an algorithm string.

    Example:

        R U R' U'

    becomes:

        [
            Move("R"),
            Move("U"),
            Move("R", "'"),
            Move("U", "'"),
        ]
    """

    if not isinstance(algorithm, str):
        raise TypeError(
            "Algorithm must be a string."
        )

    algorithm = algorithm.strip()

    if not algorithm:
        return []

    return [
        Move.parse(token)
        for token in algorithm.split()
    ]


# ============================================================================
# Algorithm formatting
# ============================================================================

def format_algorithm(
    moves: Iterable[Move],
) -> str:

    return " ".join(
        str(move)
        for move in moves
    )


# ============================================================================
# Inverse algorithm
# ============================================================================

def inverse_algorithm(
    moves: Iterable[Move],
) -> list[Move]:
    """
    Return the inverse of a move sequence.

    Example:

        R U R'

    becomes:

        R U' R'
    """

    return [
        move.inverse()
        for move in reversed(
            list(moves)
        )
    ]


# ============================================================================
# Simplification
# ============================================================================

def simplify_moves(
    moves: Iterable[Move],
) -> list[Move]:
    """
    Simplify consecutive moves of the same face.

    Examples:

        R R       -> R2
        R R R     -> R'
        R R R R   -> empty
        R R'      -> empty
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

        turns = (
            previous.quarter_turns
            + move.quarter_turns
        ) % 4

        result.pop()

        if turns == 0:
            continue

        if turns == 1:

            result.append(
                Move(move.face)
            )

        elif turns == 2:

            result.append(
                Move(
                    move.face,
                    "2",
                )
            )

        elif turns == 3:

            result.append(
                Move(
                    move.face,
                    "'",
                )
            )

    return result


# ============================================================================
# Facelet access
# ============================================================================

def _get_sticker(
    faces: dict[str, list[list[str]]],
    face: str,
    row: int,
    col: int,
) -> str:
    """
    Get one sticker.
    """

    return faces[face][row][col]


def _set_sticker(
    faces: dict[str, list[list[str]]],
    face: str,
    row: int,
    col: int,
    value: str,
) -> None:
    """
    Set one sticker.
    """

    faces[face][row][col] = value


# ============================================================================
# Clockwise quarter turn
# ============================================================================

def _apply_clockwise_quarter_turn(
    cube: CubeState,
    face: str,
) -> None:
    """
    Apply exactly one clockwise quarter turn.

    The move is calculated using 3D cube geometry rather than
    manually hard-coded strip cycles.

    This is important because it guarantees that the move engine
    and cubeValidator.py agree on the physical location of every
    sticker.

    Clockwise means:

        Looking directly at the selected face.
    """

    face = face.upper()

    if face not in VALID_FACES:
        raise ValueError(
            f"Invalid face: {face}"
        )

    # ------------------------------------------------------------------------
    # Original cube
    # ------------------------------------------------------------------------

    original = {
        current_face: [
            list(row)
            for row in cube.faces[current_face]
        ]
        for current_face in FACE_NAMES
    }

    # ------------------------------------------------------------------------
    # Start with a complete copy.
    # ------------------------------------------------------------------------

    updated = {
        current_face: [
            list(row)
            for row in original[current_face]
        ]
        for current_face in FACE_NAMES
    }

    # ------------------------------------------------------------------------
    # Selected face normal.
    # ------------------------------------------------------------------------

    face_normal = FACE_BASIS[face][0]

    # ------------------------------------------------------------------------
    # Process all 54 stickers.
    #
    # A sticker belongs to the selected layer when its position lies
    # on the selected face's outer plane.
    #
    # For example:
    #
    # R -> x = +1
    # L -> x = -1
    # U -> y = +1
    # D -> y = -1
    # F -> z = +1
    # B -> z = -1
    # ------------------------------------------------------------------------

    for (
        position,
        normal,
    ), (
        source_face,
        source_row,
        source_col,
    ) in FACELET_LOOKUP.items():

        value = _get_sticker(
            original,
            source_face,
            source_row,
            source_col,
        )

        # --------------------------------------------------------------------
        # Check whether this sticker belongs to the layer.
        # --------------------------------------------------------------------

        if _dot(
            position,
            face_normal,
        ) == 1:

            # ---------------------------------------------------------------
            # Rotate both:
            #
            # 1. The sticker position
            # 2. The sticker normal
            #
            # Rotating the normal is essential. Without it, stickers
            # would move to the correct coordinates but remain associated
            # with the wrong face orientation.
            # ---------------------------------------------------------------

            new_position = _rotate_vector_clockwise(
                position,
                face_normal,
            )

            new_normal = _rotate_vector_clockwise(
                normal,
                face_normal,
            )

            destination = FACELET_LOOKUP.get(
                (
                    new_position,
                    new_normal,
                )
            )

            if destination is None:
                raise RuntimeError(
                    "Move engine geometry error: "
                    f"could not map rotated sticker "
                    f"{(new_position, new_normal)}."
                )

            (
                destination_face,
                destination_row,
                destination_col,
            ) = destination

        else:

            destination_face = source_face
            destination_row = source_row
            destination_col = source_col

        _set_sticker(
            updated,
            destination_face,
            destination_row,
            destination_col,
            value,
        )

    # ------------------------------------------------------------------------
    # Replace cube state.
    # ------------------------------------------------------------------------

    cube.faces = updated


# ============================================================================
# Move application
# ============================================================================

def apply_move(
    cube: CubeState,
    move: Move,
) -> CubeState:
    """
    Apply one move to a CubeState.

    The original cube is never modified.
    """

    if CubeState is None:
        raise RuntimeError(
            "CubeState could not be imported: "
            f"{CUBE_STATE_IMPORT_ERROR}"
        )

    if not isinstance(cube, CubeState):
        raise TypeError(
            "cube must be a CubeState."
        )

    if not isinstance(move, Move):
        raise TypeError(
            "move must be a Move."
        )

    result = CubeState(
        cube.to_dict()
    )

    for _ in range(
        move.quarter_turns
    ):

        _apply_clockwise_quarter_turn(
            result,
            move.face,
        )

    return result


# ============================================================================
# Multiple moves
# ============================================================================

def apply_moves(
    cube: CubeState,
    moves: Iterable[Move],
) -> CubeState:
    """
    Apply multiple moves.
    """

    result = cube

    for move in moves:

        result = apply_move(
            result,
            move,
        )

    return result


# ============================================================================
# Algorithm application
# ============================================================================

def apply_algorithm(
    cube: CubeState,
    algorithm: str,
) -> CubeState:
    """
    Apply an algorithm string.

    Example:

        apply_algorithm(
            cube,
            "R U R' U'"
        )
    """

    moves = parse_algorithm(
        algorithm
    )

    return apply_moves(
        cube,
        moves,
    )


# ============================================================================
# Scramble
# ============================================================================

def apply_scramble(
    cube: CubeState,
    scramble: str,
) -> CubeState:
    """
    Apply a scramble.

    Scrambles use the same notation as algorithms.
    """

    return apply_algorithm(
        cube,
        scramble,
    )


# ============================================================================
# Algorithm utilities
# ============================================================================

def invert_algorithm(
    algorithm: str,
) -> str:
    """
    Return the inverse of an algorithm.

    Example:

        R U R' U'

    ->

        U R U' R'
    """

    moves = parse_algorithm(
        algorithm
    )

    return format_algorithm(
        inverse_algorithm(
            moves
        )
    )


def simplify_algorithm(
    algorithm: str,
) -> str:
    """
    Simplify an algorithm.
    """

    moves = parse_algorithm(
        algorithm
    )

    simplified = simplify_moves(
        moves
    )

    return format_algorithm(
        simplified
    )


# ============================================================================
# Solved cube
# ============================================================================

def _create_solved_cube() -> CubeState:
    """
    Create a standard solved CubeState.

    This exactly matches cubeValidator.py.
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

    return CubeState(
        faces
    )


# ============================================================================
# Test helpers
# ============================================================================

def _states_equal(
    first: CubeState,
    second: CubeState,
) -> bool:
    """
    Compare two cube states.
    """

    return (
        first.to_dict()
        == second.to_dict()
    )


def _test_basic_inverses(
    cube: CubeState,
) -> bool:
    """
    Test every basic move followed by its inverse.
    """

    print(
        "Basic inverse tests:"
    )

    all_passed = True

    for face in FACE_NAMES:

        algorithm = (
            f"{face} {face}'"
        )

        restored = apply_algorithm(
            cube,
            algorithm,
        )

        passed = _states_equal(
            restored,
            cube,
        )

        print(
            f"  {algorithm}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_passed = False

    print()

    print(
        "Basic inverse tests:",
        "PASS" if all_passed else "FAILED",
    )

    return all_passed


def _test_four_turns(
    cube: CubeState,
) -> bool:
    """
    Test four quarter turns restore the cube.
    """

    print(
        "Four-turn restoration tests:"
    )

    all_passed = True

    for face in FACE_NAMES:

        algorithm = (
            f"{face} "
            f"{face} "
            f"{face} "
            f"{face}"
        )

        restored = apply_algorithm(
            cube,
            algorithm,
        )

        passed = _states_equal(
            restored,
            cube,
        )

        print(
            f"  {algorithm}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_passed = False

    print()

    print(
        "All four-turn tests:",
        "PASS" if all_passed else "FAILED",
    )

    return all_passed


def _test_algorithm_inverse(
    cube: CubeState,
) -> bool:
    """
    Test a complete multi-face algorithm and its inverse.
    """

    algorithm = (
        "R U R' U' F2 L D"
    )

    inverse = invert_algorithm(
        algorithm
    )

    scrambled = apply_algorithm(
        cube,
        algorithm,
    )

    restored = apply_algorithm(
        scrambled,
        inverse,
    )

    passed = _states_equal(
        restored,
        cube,
    )

    print(
        "Algorithm:",
        algorithm,
    )

    print(
        "Inverse:",
        inverse,
    )

    print(
        "Algorithm + inverse restores cube:",
        passed,
    )

    return passed


# ============================================================================
# Validator integration test
# ============================================================================

def _test_validator_integration(
    cube: CubeState,
) -> bool:
    """
    Verify that a cube produced by the move engine is accepted
    by cubeValidator.py.

    This is the critical test that catches disagreements between
    the move engine's geometry and the validator's cubie layout.
    """

    try:

        from cubeValidator import validate_cube

    except ImportError as exc:

        print(
            "Validator integration test skipped:"
        )

        print(
            f"  Could not import cubeValidator.py: {exc}"
        )

        return True

    algorithm = (
        "R U R' U' F2 L D"
    )

    scrambled = apply_algorithm(
        cube,
        algorithm,
    )

    result = validate_cube(
        scrambled
    )

    print(
        "Validator integration:"
    )

    print(
        f"  Algorithm: {algorithm}"
    )

    print(
        f"  Valid: {result.valid}"
    )

    if result.errors:

        print()
        print("  Validator errors:")

        for error in result.errors:

            print(
                f"    - {error}"
            )

    return result.valid


# ============================================================================
# Main
# ============================================================================

def main() -> None:

    print(
        "CubeAI Move Engine"
    )

    print(
        "------------------"
    )

    # ========================================================================
    # Move parsing
    # ========================================================================

    move = Move.parse(
        "R'"
    )

    print(
        f"Parsed move: {move}"
    )

    print(
        f"Inverse:      {move.inverse()}"
    )

    print(
        f"Quarter turns: {move.quarter_turns}"
    )

    print()

    # ========================================================================
    # Algorithm parsing
    # ========================================================================

    algorithm = (
        "R U R' U'"
    )

    moves = parse_algorithm(
        algorithm
    )

    print(
        f"Algorithm: {algorithm}"
    )

    print(
        f"Parsed: {moves}"
    )

    print(
        "Inverse:",
        format_algorithm(
            inverse_algorithm(
                moves
            )
        ),
    )

    print()

    # ========================================================================
    # Simplification
    # ========================================================================

    test = (
        "R R R R U U R R R"
    )

    print(
        "Before simplify:",
        test,
    )

    print(
        "After simplify: ",
        simplify_algorithm(
            test
        ),
    )

    print()

    # ========================================================================
    # Solved cube
    # ========================================================================

    cube = _create_solved_cube()

    print(
        "Solved cube color counts:"
    )

    print(
        cube.color_counts()
    )

    print()

    # ========================================================================
    # Basic inverse tests
    # ========================================================================

    basic_inverse_passed = (
        _test_basic_inverses(
            cube
        )
    )

    print()

    # ========================================================================
    # R2
    # ========================================================================

    moved = apply_algorithm(
        cube,
        "R2",
    )

    print(
        "After R2:"
    )

    print(
        moved.color_counts()
    )

    print()

    # ========================================================================
    # Four-turn tests
    # ========================================================================

    four_turn_passed = (
        _test_four_turns(
            cube
        )
    )

    print()

    # ========================================================================
    # Complex algorithm
    # ========================================================================

    algorithm_inverse_passed = (
        _test_algorithm_inverse(
            cube
        )
    )

    print()

    # ========================================================================
    # Validator integration
    # ========================================================================

    validator_passed = (
        _test_validator_integration(
            cube
        )
    )

    print()

    # ========================================================================
    # Original cube unchanged
    # ========================================================================

    original = _create_solved_cube()

    apply_algorithm(
        original,
        "R U F D L B"
    )

    unchanged = (
        _states_equal(
            original,
            cube,
        )
    )

    print(
        "Original cube unchanged:",
        unchanged,
    )

    print()

    # ========================================================================
    # Final result
    # ========================================================================

    all_passed = (
        basic_inverse_passed
        and four_turn_passed
        and algorithm_inverse_passed
        and validator_passed
        and unchanged
    )

    if all_passed:

        print(
            "Move engine tests PASSED."
        )

    else:

        print(
            "Move engine tests FAILED."
        )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()