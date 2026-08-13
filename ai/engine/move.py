"""
CubeAI - Move Engine

Defines Rubik's Cube moves and applies them to CubeState.

The move engine uses the exact face layout and cubie orientation
conventions defined by cubeValidator.py.

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

FACE_COLORS = {
    "U": "white",
    "R": "red",
    "F": "green",
    "D": "yellow",
    "L": "orange",
    "B": "blue",
}


# ============================================================================
# 3D geometry
# ============================================================================

Vector = tuple[int, int, int]


# ---------------------------------------------------------------------------
# Face basis
#
# Each face contains:
#
#     normal
#     right
#     down
#
# The basis is deliberately matched to cubeValidator.py.
#
# U:
#     right = +X
#     down  = +Z
#
# R:
#     right = -Z
#     down  = -Y
#
# F:
#     right = +X
#     down  = -Y
#
# D:
#     right = +X
#     down  = -Z
#
# L:
#     right = +Z
#     down  = -Y
#
# B:
#     right = -X
#     down  = -Y
# ---------------------------------------------------------------------------

FACE_BASIS: dict[
    str,
    tuple[Vector, Vector, Vector],
] = {

    "U": (
        (0, 1, 0),
        (1, 0, 0),
        (0, 0, 1),
    ),

    "R": (
        (1, 0, 0),
        (0, 0, -1),
        (0, -1, 0),
    ),

    "F": (
        (0, 0, 1),
        (1, 0, 0),
        (0, -1, 0),
    ),

    "D": (
        (0, -1, 0),
        (1, 0, 0),
        (0, 0, -1),
    ),

    "L": (
        (-1, 0, 0),
        (0, 0, 1),
        (0, -1, 0),
    ),

    "B": (
        (0, 0, -1),
        (-1, 0, 0),
        (0, -1, 0),
    ),
}


# ============================================================================
# Vector helpers
# ============================================================================

def _dot(
    a: Vector,
    b: Vector,
) -> int:
    return (
        a[0] * b[0]
        + a[1] * b[1]
        + a[2] * b[2]
    )


def _cross(
    a: Vector,
    b: Vector,
) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _scale(
    vector: Vector,
    scalar: int,
) -> Vector:
    return (
        vector[0] * scalar,
        vector[1] * scalar,
        vector[2] * scalar,
    )


def _add(
    a: Vector,
    b: Vector,
) -> Vector:
    return (
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2],
    )


# ============================================================================
# Facelet geometry lookup
# ============================================================================

FACELET_LOOKUP: dict[
    tuple[Vector, Vector],
    tuple[str, int, int],
] = {}


def _build_facelet_lookup() -> None:
    """
    Build the physical mapping for all 54 stickers.

    A sticker is identified by:

        (3D position, sticker normal)

    which uniquely identifies its destination after a rotation.
    """

    FACELET_LOOKUP.clear()

    for face in FACE_NAMES:

        normal, right, down = FACE_BASIS[face]

        for row in range(3):

            for col in range(3):

                column_offset = col - 1
                row_offset = row - 1

                position = _add(
                    normal,
                    _add(
                        _scale(
                            right,
                            column_offset,
                        ),
                        _scale(
                            down,
                            row_offset,
                        ),
                    ),
                )

                key = (
                    position,
                    normal,
                )

                if key in FACELET_LOOKUP:
                    raise RuntimeError(
                        "Duplicate facelet geometry detected: "
                        f"{key}"
                    )

                FACELET_LOOKUP[key] = (
                    face,
                    row,
                    col,
                )


_build_facelet_lookup()


# ============================================================================
# Rotation
# ============================================================================

def _rotate_clockwise(
    vector: Vector,
    normal: Vector,
) -> Vector:
    """
    Rotate a vector 90 degrees clockwise when looking directly
    at the selected face.

    This is a -90 degree rotation around the face normal.

    Rodrigues rotation:

        v' = -n x v + n(n . v)
    """

    cross = _cross(
        normal,
        vector,
    )

    projection = _dot(
        normal,
        vector,
    )

    return (
        -cross[0]
        + normal[0] * projection,

        -cross[1]
        + normal[1] * projection,

        -cross[2]
        + normal[2] * projection,
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
        Number of clockwise quarter turns.

            R  = 1
            R2 = 2
            R' = 3
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


def format_algorithm(
    moves: Iterable[Move],
) -> str:

    return " ".join(
        str(move)
        for move in moves
    )


# ============================================================================
# Algorithm inversion
# ============================================================================

def inverse_algorithm(
    moves: Iterable[Move],
) -> list[Move]:

    return [
        move.inverse()
        for move in reversed(
            list(moves)
        )
    ]


def invert_algorithm(
    algorithm: str,
) -> str:

    return format_algorithm(
        inverse_algorithm(
            parse_algorithm(algorithm)
        )
    )


# ============================================================================
# Move simplification
# ============================================================================

def simplify_moves(
    moves: Iterable[Move],
) -> list[Move]:

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


def simplify_algorithm(
    algorithm: str,
) -> str:

    return format_algorithm(
        simplify_moves(
            parse_algorithm(algorithm)
        )
    )


# ============================================================================
# Cube copying
# ============================================================================

def _copy_faces(
    cube: CubeState,
) -> dict[str, list[list[str]]]:
    """
    Deep-copy every face.

    Do NOT rely on CubeState.to_dict() here.

    The move engine must guarantee that applying a move never
    mutates the original CubeState.
    """

    return {
        face: [
            list(row)
            for row in cube.faces[face]
        ]
        for face in FACE_NAMES
    }


# ============================================================================
# Single clockwise quarter turn
# ============================================================================

def _apply_clockwise_quarter_turn(
    cube: CubeState,
    face: str,
) -> None:
    """
    Apply exactly one clockwise quarter turn.

    The transformation is performed on physical sticker
    coordinates.

    Both the sticker position AND sticker normal are rotated.

    This is critical.

    Rotating only the position creates states that can look
    superficially correct while producing impossible cubie
    orientations.
    """

    face = face.upper()

    if face not in VALID_FACES:
        raise ValueError(
            f"Invalid face: {face}"
        )

    original = _copy_faces(cube)

    updated = {
        current_face: [
            list(row)
            for row in original[current_face]
        ]
        for current_face in FACE_NAMES
    }

    face_normal = FACE_BASIS[face][0]

    for (
        position,
        normal,
    ), (
        source_face,
        source_row,
        source_col,
    ) in FACELET_LOOKUP.items():

        value = original[
            source_face
        ][
            source_row
        ][
            source_col
        ]

        # ---------------------------------------------------------------
        # Is this sticker part of the selected layer?
        #
        # Since every outer face has coordinate +1 or -1:
        #
        #     R -> x = +1
        #     L -> x = -1
        #     U -> y = +1
        #     D -> y = -1
        #     F -> z = +1
        #     B -> z = -1
        # ---------------------------------------------------------------

        if _dot(
            position,
            face_normal,
        ) == 1:

            new_position = _rotate_clockwise(
                position,
                face_normal,
            )

            new_normal = _rotate_clockwise(
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
                    "Move engine geometry error.\n"
                    f"Move: {face}\n"
                    f"Source: "
                    f"{(position, normal)}\n"
                    f"Destination: "
                    f"{(new_position, new_normal)}"
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

        updated[
            destination_face
        ][
            destination_row
        ][
            destination_col
        ] = value

    cube.faces = updated


# ============================================================================
# Apply move
# ============================================================================

def apply_move(
    cube: CubeState,
    move: Move,
) -> CubeState:
    """
    Apply one move without modifying the original cube.
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

    # ---------------------------------------------------------------
    # Explicit deep copy.
    # ---------------------------------------------------------------

    result = CubeState(
        _copy_faces(cube)
    )

    # ---------------------------------------------------------------
    # Convert R/R'/R2 into clockwise quarter turns.
    # ---------------------------------------------------------------

    for _ in range(
        move.quarter_turns
    ):

        _apply_clockwise_quarter_turn(
            result,
            move.face,
        )

    return result


# ============================================================================
# Apply multiple moves
# ============================================================================

def apply_moves(
    cube: CubeState,
    moves: Iterable[Move],
) -> CubeState:

    result = cube

    for move in moves:

        result = apply_move(
            result,
            move,
        )

    return result


# ============================================================================
# Apply algorithm
# ============================================================================

def apply_algorithm(
    cube: CubeState,
    algorithm: str,
) -> CubeState:

    return apply_moves(
        cube,
        parse_algorithm(algorithm),
    )


def apply_scramble(
    cube: CubeState,
    scramble: str,
) -> CubeState:

    return apply_algorithm(
        cube,
        scramble,
    )


# ============================================================================
# Solved cube
# ============================================================================

def _create_solved_cube() -> CubeState:

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


# ============================================================================
# State comparison
# ============================================================================

def _states_equal(
    first: CubeState,
    second: CubeState,
) -> bool:

    return (
        first.to_dict()
        == second.to_dict()
    )


# ============================================================================
# Validator integration
# ============================================================================

def _validate_algorithm(
    cube: CubeState,
    algorithm: str,
) -> bool:

    try:

        from cubeValidator import validate_cube

    except ImportError as exc:

        print(
            "  Validator unavailable:",
            exc,
        )

        return True

    scrambled = apply_algorithm(
        cube,
        algorithm,
    )

    result = validate_cube(
        scrambled
    )

    print(
        f"  {algorithm}: "
        f"{'PASS' if result.valid else 'FAIL'}"
    )

    if not result.valid:

        for error in result.errors:

            print(
                f"    - {error}"
            )

    return result.valid


def _test_validator_integration(
    cube: CubeState,
) -> bool:

    print(
        "Validator integration tests:"
    )

    algorithms = (
        "R",
        "U",
        "F",
        "D",
        "L",
        "B",
        "R U R' U'",
        "R U R' U' F2",
        "R U R' U' F2 L D",
        "R U R' U' F2 L D B R2 U2",
        "F R U R' U' F'",
        "R2 U2 F2 D2 L2 B2",
    )

    all_passed = True

    for algorithm in algorithms:

        passed = _validate_algorithm(
            cube,
            algorithm,
        )

        if not passed:
            all_passed = False

    print()

    print(
        "Validator integration:",
        "PASS" if all_passed else "FAILED",
    )

    return all_passed


# ============================================================================
# Basic inverse tests
# ============================================================================

def _test_basic_inverses(
    cube: CubeState,
) -> bool:

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


# ============================================================================
# Four-turn tests
# ============================================================================

def _test_four_turns(
    cube: CubeState,
) -> bool:

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


# ============================================================================
# Algorithm inverse test
# ============================================================================

def _test_algorithm_inverse(
    cube: CubeState,
) -> bool:

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
# Original cube immutability
# ============================================================================

def _test_original_unchanged(
    cube: CubeState,
) -> bool:

    original = _create_solved_cube()

    moved = apply_algorithm(
        original,
        "R U F D L B",
    )

    original_unchanged = _states_equal(
        original,
        cube,
    )

    moved_differs = not _states_equal(
        moved,
        cube,
    )

    print(
        "Original cube unchanged:",
        original_unchanged,
    )

    print(
        "Returned moved cube differs:",
        moved_differs,
    )

    return (
        original_unchanged
        and moved_differs
    )


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

    print()

    # ------------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------------

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
            inverse_algorithm(moves)
        ),
    )

    print()

    # ------------------------------------------------------------------------
    # Simplification
    # ------------------------------------------------------------------------

    test = (
        "R R R R U U R R R"
    )

    print(
        "Before simplify:",
        test,
    )

    print(
        "After simplify: ",
        simplify_algorithm(test),
    )

    print()

    # ------------------------------------------------------------------------
    # Solved cube
    # ------------------------------------------------------------------------

    cube = _create_solved_cube()

    print(
        "Solved cube color counts:"
    )

    print(
        cube.color_counts()
    )

    print()

    # ------------------------------------------------------------------------
    # Basic tests
    # ------------------------------------------------------------------------

    basic_passed = _test_basic_inverses(
        cube
    )

    print()

    # ------------------------------------------------------------------------
    # R2
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # Four turns
    # ------------------------------------------------------------------------

    four_turn_passed = _test_four_turns(
        cube
    )

    print()

    # ------------------------------------------------------------------------
    # Algorithm inverse
    # ------------------------------------------------------------------------

    algorithm_inverse_passed = (
        _test_algorithm_inverse(
            cube
        )
    )

    print()

    # ------------------------------------------------------------------------
    # Validator
    # ------------------------------------------------------------------------

    validator_passed = (
        _test_validator_integration(
            cube
        )
    )

    print()

    # ------------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------------

    unchanged_passed = (
        _test_original_unchanged(
            cube
        )
    )

    print()

    # ------------------------------------------------------------------------
    # Final
    # ------------------------------------------------------------------------

    all_passed = (
        basic_passed
        and four_turn_passed
        and algorithm_inverse_passed
        and validator_passed
        and unchanged_passed
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