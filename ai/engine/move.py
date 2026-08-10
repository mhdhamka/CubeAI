
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

Example algorithm:

    R U R' U'

This module is responsible for move representation and
move application.

It does NOT solve the cube.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Iterable


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
# Face normals
# ============================================================================

FACE_NORMALS = {
    FACE_U: (0, 1, 0),
    FACE_R: (1, 0, 0),
    FACE_F: (0, 0, 1),
    FACE_D: (0, -1, 0),
    FACE_L: (-1, 0, 0),
    FACE_B: (0, 0, -1),
}


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
            return Move(self.face, "'")

        if self.modifier == "'":
            return Move(self.face)

        return Move(self.face, "2")

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
# Move application
# ============================================================================

def apply_move(
    cube: CubeState,
    move: Move,
) -> CubeState:
    """
    Apply one move to a CubeState.

    The original cube is never modified.

    Sticker position AND sticker orientation are tracked
    during rotation. This is important because an edge or
    corner coordinate can belong to multiple faces.
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

    for _ in range(move.quarter_turns):

        _apply_clockwise_quarter_turn(
            result,
            move.face,
        )

    return result


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


def apply_algorithm(
    cube: CubeState,
    algorithm: str,
) -> CubeState:

    moves = parse_algorithm(
        algorithm
    )

    return apply_moves(
        cube,
        moves,
    )


# ============================================================================
# Face rotation
# ============================================================================

def _rotate_face_clockwise(
    face: list[list[str]],
) -> list[list[str]]:
    """
    Rotate a 3x3 face clockwise.

        a b c          g d a
        d e f   ->     h e b
        g h i          i f c
    """

    return [
        [
            face[2][0],
            face[1][0],
            face[0][0],
        ],
        [
            face[2][1],
            face[1][1],
            face[0][1],
        ],
        [
            face[2][2],
            face[1][2],
            face[0][2],
        ],
    ]


# ============================================================================
# Sticker position
# ============================================================================

def _face_to_coordinates(
    face: str,
    row: int,
    col: int,
) -> tuple[int, int, int]:
    """
    Convert face row/column into a 3D sticker position.
    """

    if face == FACE_F:
        return (
            col - 1,
            1 - row,
            1,
        )

    if face == FACE_B:
        return (
            1 - col,
            1 - row,
            -1,
        )

    if face == FACE_U:
        return (
            col - 1,
            1,
            row - 1,
        )

    if face == FACE_D:
        return (
            col - 1,
            -1,
            1 - row,
        )

    if face == FACE_R:
        return (
            1,
            1 - row,
            1 - col,
        )

    if face == FACE_L:
        return (
            -1,
            1 - row,
            col - 1,
        )

    raise ValueError(
        f"Invalid face: {face}"
    )


# ============================================================================
# Sticker position -> face
# ============================================================================

def _coordinates_to_face_position(
    face: str,
    x: int,
    y: int,
    z: int,
) -> tuple[int, int]:
    """
    Convert a position on a known face into row/column.

    The destination face is determined separately from
    the sticker normal.
    """

    if face == FACE_F:
        return (
            1 - y,
            x + 1,
        )

    if face == FACE_B:
        return (
            1 - y,
            1 - x,
        )

    if face == FACE_U:
        return (
            z + 1,
            x + 1,
        )

    if face == FACE_D:
        return (
            1 - z,
            x + 1,
        )

    if face == FACE_R:
        return (
            1 - y,
            1 - z,
        )

    if face == FACE_L:
        return (
            1 - y,
            z + 1,
        )

    raise ValueError(
        f"Invalid face: {face}"
    )


# ============================================================================
# Coordinate rotation
# ============================================================================

def _rotate_coordinate(
    coordinate: tuple[int, int, int],
    axis: str,
    clockwise: bool = True,
) -> tuple[int, int, int]:
    """
    Rotate a coordinate by 90 degrees.
    """

    x, y, z = coordinate

    if axis == "x":

        if clockwise:
            return (
                x,
                z,
                -y,
            )

        return (
            x,
            -z,
            y,
        )

    if axis == "y":

        if clockwise:
            return (
                z,
                y,
                -x,
            )

        return (
            -z,
            y,
            x,
        )

    if axis == "z":

        if clockwise:
            return (
                y,
                -x,
                z,
            )

        return (
            -y,
            x,
            z,
        )

    raise ValueError(
        f"Invalid rotation axis: {axis}"
    )


# ============================================================================
# Normal -> face
# ============================================================================

def _normal_to_face(
    normal: tuple[int, int, int],
) -> str:

    for face, face_normal in FACE_NORMALS.items():

        if normal == face_normal:
            return face

    raise ValueError(
        f"Invalid sticker normal: {normal}"
    )


# ============================================================================
# Clockwise face turn
# ============================================================================

def _apply_clockwise_quarter_turn(
    cube: CubeState,
    face: str,
) -> None:
    """
    Apply one clockwise quarter turn.

    This implementation rotates BOTH:

        1. sticker position
        2. sticker orientation / normal

    This avoids ambiguity at edges and corners.
    """

    face = face.upper()

    if face not in VALID_FACES:
        raise ValueError(
            f"Invalid face: {face}"
        )

    # ------------------------------------------------------------------------
    # Copy original cube.
    # ------------------------------------------------------------------------

    original = cube.to_dict()

    # ------------------------------------------------------------------------
    # Determine axis and layer.
    # ------------------------------------------------------------------------

    if face == FACE_R:
        axis = "x"
        layer = 1

    elif face == FACE_L:
        axis = "x"
        layer = -1

    elif face == FACE_U:
        axis = "y"
        layer = 1

    elif face == FACE_D:
        axis = "y"
        layer = -1

    elif face == FACE_F:
        axis = "z"
        layer = 1

    elif face == FACE_B:
        axis = "z"
        layer = -1

    else:
        raise ValueError(
            f"Invalid face: {face}"
        )

    # ------------------------------------------------------------------------
    # Opposite faces rotate in the opposite global direction so that
    # the move is clockwise when looking directly at that face.
    # ------------------------------------------------------------------------

    clockwise = face not in (
        FACE_L,
        FACE_D,
        FACE_B,
    )

    # ------------------------------------------------------------------------
    # Start from an exact copy of the original state.
    # ------------------------------------------------------------------------

    cube.faces = {
        current_face: [
            list(row)
            for row in original[current_face]
        ]
        for current_face in FACE_NAMES
    }

    # ------------------------------------------------------------------------
    # Move every sticker on the selected layer.
    # ------------------------------------------------------------------------

    for source_face in FACE_NAMES:

        source_normal = FACE_NORMALS[
            source_face
        ]

        for row in range(GRID_SIZE):

            for col in range(GRID_SIZE):

                position = _face_to_coordinates(
                    source_face,
                    row,
                    col,
                )

                x, y, z = position

                # ------------------------------------------------------------
                # Only stickers physically located on the selected layer
                # participate in this move.
                # ------------------------------------------------------------

                if axis == "x" and x != layer:
                    continue

                if axis == "y" and y != layer:
                    continue

                if axis == "z" and z != layer:
                    continue

                # ------------------------------------------------------------
                # Rotate sticker position.
                # ------------------------------------------------------------

                destination_position = _rotate_coordinate(
                    position,
                    axis,
                    clockwise,
                )

                # ------------------------------------------------------------
                # Rotate sticker normal.
                #
                # This is the critical part that fixes the previous engine.
                # ------------------------------------------------------------

                destination_normal = _rotate_coordinate(
                    source_normal,
                    axis,
                    clockwise,
                )

                destination_face = _normal_to_face(
                    destination_normal
                )

                destination_row, destination_col = (
                    _coordinates_to_face_position(
                        destination_face,
                        *destination_position,
                    )
                )

                cube.faces[
                    destination_face
                ][
                    destination_row
                ][
                    destination_col
                ] = original[
                    source_face
                ][
                    row
                ][
                    col
                ]


# ============================================================================
# Scramble
# ============================================================================

def apply_scramble(
    cube: CubeState,
    scramble: str,
) -> CubeState:

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
# Demo
# ============================================================================

def _create_solved_cube() -> CubeState:
    """
    Create a standard solved cube.
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


def main() -> None:

    print(
        "CubeAI Move Engine"
    )

    print(
        "------------------"
    )

    # ------------------------------------------------------------------------
    # Parse move
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
        f"Quarter turns: "
        f"{move.quarter_turns}"
    )

    print()

    # ------------------------------------------------------------------------
    # Parse algorithm
    # ------------------------------------------------------------------------

    algorithm = "R U R' U'"

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
        f"Inverse: "
        f"{format_algorithm(inverse_algorithm(moves))}"
    )

    print()

    # ------------------------------------------------------------------------
    # Simplification
    # ------------------------------------------------------------------------

    test = "R R R R U U R R R"

    print(
        f"Before simplify: "
        f"{test}"
    )

    print(
        f"After simplify:  "
        f"{simplify_algorithm(test)}"
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

    # ------------------------------------------------------------------------
    # R + R'
    # ------------------------------------------------------------------------

    moved = apply_algorithm(
        cube,
        "R R'",
    )

    print()

    print(
        "After R R':"
    )

    print(
        moved.color_counts()
    )

    print(
        "State restored:",
        moved.to_dict()
        == cube.to_dict(),
    )

    # ------------------------------------------------------------------------
    # R2
    # ------------------------------------------------------------------------

    moved = apply_algorithm(
        cube,
        "R2",
    )

    print()

    print(
        "After R2:"
    )

    print(
        moved
    )

    # ------------------------------------------------------------------------
    # Four R rotations
    # ------------------------------------------------------------------------

    restored = apply_algorithm(
        cube,
        "R R R R",
    )

    print()

    print(
        "R R R R restores cube:",
        restored.to_dict()
        == cube.to_dict(),
    )

    # ------------------------------------------------------------------------
    # Algorithm + inverse
    # ------------------------------------------------------------------------

    algorithm = "R U R' U' F2 L D"

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

    print()

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
        restored.to_dict()
        == cube.to_dict(),
    )

    # ------------------------------------------------------------------------
    # Additional move tests
    # ------------------------------------------------------------------------

    print()

    print(
        "Move restoration tests:"
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

        passed = (
            restored.to_dict()
            == cube.to_dict()
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
        "PASS" if all_passed else "FAIL",
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()
