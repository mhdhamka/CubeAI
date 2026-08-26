"""
CubeAI - Move Engine

Defines Rubik's Cube moves and applies them to:

    1. CubeState   - sticker/face representation
    2. CubieState  - physical piece representation

The move engine uses the exact face layout and cubie orientation
conventions defined by cubeValidator.py and cubie.py.

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


try:
    from cubie import (
        CubieState,
        CornerCubie,
        EdgeCubie,
    )
except ImportError as exc:
    CubieState = None
    CornerCubie = None
    EdgeCubie = None
    CUBIE_IMPORT_ERROR = str(exc)
else:
    CUBIE_IMPORT_ERROR = None


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

COLOR_TO_FACE = {
    "white": "U",
    "red": "R",
    "green": "F",
    "yellow": "D",
    "orange": "L",
    "blue": "B",
}


# ============================================================================
# Cubie names
# ============================================================================

CORNER_NAMES = (
    "UFR",
    "URB",
    "UBL",
    "ULF",
    "DFR",
    "DRB",
    "DBL",
    "DLF",
)

EDGE_NAMES = (
    "UF",
    "UR",
    "UB",
    "UL",
    "FR",
    "RB",
    "BL",
    "LF",
    "DF",
    "DR",
    "DB",
    "DL",
)


# ============================================================================
# 3D geometry
# ============================================================================

Vector = tuple[int, int, int]


# ---------------------------------------------------------------------------
# Face basis
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
# Piece geometry
# ============================================================================

def _face_normal(face: str) -> Vector:
    """
    Return the 3D normal vector for a face.
    """

    return FACE_BASIS[face][0]


def _piece_position(name: str) -> Vector:
    """
    Convert a cubie name into its physical 3D position.

    Example:

        UFR -> (+1, +1, +1)
        DBL -> (-1, -1, -1)
    """

    position = (0, 0, 0)

    for face in name:
        position = _add(
            position,
            _face_normal(face),
        )

    return position


CORNER_POSITION_LOOKUP = {
    _piece_position(name): index
    for index, name in enumerate(CORNER_NAMES)
}

EDGE_POSITION_LOOKUP = {
    _piece_position(name): index
    for index, name in enumerate(EDGE_NAMES)
}


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
# CubeState helpers
# ============================================================================

def _copy_faces(
    cube: CubeState,
) -> dict[str, list[list[str]]]:

    return {
        face: [
            list(row)
            for row in cube.faces[face]
        ]
        for face in FACE_NAMES
    }


# ============================================================================
# CubeState - single clockwise quarter turn
# ============================================================================

def _apply_clockwise_quarter_turn(
    cube: CubeState,
    face: str,
) -> None:

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
# CubeState - apply move
# ============================================================================

def apply_move(
    cube: CubeState,
    move: Move,
) -> CubeState:

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
        _copy_faces(cube)
    )

    for _ in range(
        move.quarter_turns
    ):

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
# CubieState move helpers
# ============================================================================

# CubieState stores piece identity plus orientation.  Do not reconstruct
# sticker normals from the destination position: a moved piece can have a
# different colour set from that position.  Orientation is updated
# additively from the physical delta of each face turn.

CORNER_COLORS = {
    "UFR": ("white", "green", "red"), "URB": ("white", "red", "blue"),
    "UBL": ("white", "blue", "orange"), "ULF": ("white", "orange", "green"),
    "DFR": ("yellow", "green", "red"), "DRB": ("yellow", "red", "blue"),
    "DBL": ("yellow", "blue", "orange"), "DLF": ("yellow", "orange", "green"),
}

EDGE_COLORS = {
    "UF": ("white", "green"), "UR": ("white", "red"), "UB": ("white", "blue"),
    "UL": ("white", "orange"), "FR": ("green", "red"), "RB": ("red", "blue"),
    "BL": ("blue", "orange"), "LF": ("orange", "green"), "DF": ("yellow", "green"),
    "DR": ("yellow", "red"), "DB": ("yellow", "blue"), "DL": ("yellow", "orange"),
}


def _piece_position(piece_name: str) -> Vector:
    """Return the solved 3D position of a corner or edge."""
    x = 1 if "R" in piece_name else -1 if "L" in piece_name else 0
    y = 1 if "U" in piece_name else -1 if "D" in piece_name else 0
    z = 1 if "F" in piece_name else -1 if "B" in piece_name else 0
    return (x, y, z)


def _corner_orientation_delta(piece_name: str, face: str) -> int:
    """Return the correct per-corner orientation delta for a face turn.

    Corner orientation is piece-dependent.  R/L/F/B turns twist two
    corners by +1 and the other two by +2; using one delta for all four
    corners violates the corner-orientation sum invariant.
    """
    deltas = {
        "U": {"UFR":0,"URB":0,"UBL":0,"ULF":0,"DFR":0,"DRB":0,"DBL":0,"DLF":0},
        "D": {"UFR":0,"URB":0,"UBL":0,"ULF":0,"DFR":0,"DRB":0,"DBL":0,"DLF":0},
        "R": {"UFR":2,"URB":1,"UBL":0,"ULF":0,"DFR":1,"DRB":2,"DBL":0,"DLF":0},
        "L": {"UFR":0,"URB":0,"UBL":2,"ULF":1,"DFR":0,"DRB":0,"DBL":1,"DLF":2},
        "F": {"UFR":1,"URB":0,"UBL":0,"ULF":2,"DFR":2,"DRB":0,"DBL":0,"DLF":1},
        "B": {"UFR":0,"URB":2,"UBL":1,"ULF":0,"DFR":0,"DRB":1,"DBL":2,"DLF":0},
    }
    try:
        return deltas[face][piece_name]
    except KeyError as exc:
        raise ValueError(f"Invalid corner orientation lookup: piece={piece_name}, face={face}") from exc


def _edge_orientation_delta(piece_name: str, face: str) -> int:
    """Return the edge-orientation delta for a quarter-turn of face.

    Edge orientation (0 = good, 1 = flipped) only changes on F and B moves.
    U, D, R, L quarter turns never flip edges.

    The table below is derived from the standard HTM edge-orientation
    convention where U/D stickers (white/yellow) define orientation for
    UD-slice edges, and F/B stickers define orientation for FB-slice edges.
    """
    # Only F and B moves flip edges; U/D/R/L never do.
    deltas = {
        "U": {"UF":0,"UR":0,"UB":0,"UL":0,"FR":0,"RB":0,"BL":0,"LF":0,
              "DF":0,"DR":0,"DB":0,"DL":0},
        "D": {"UF":0,"UR":0,"UB":0,"UL":0,"FR":0,"RB":0,"BL":0,"LF":0,
              "DF":0,"DR":0,"DB":0,"DL":0},
        "R": {"UF":0,"UR":0,"UB":0,"UL":0,"FR":0,"RB":0,"BL":0,"LF":0,
              "DF":0,"DR":0,"DB":0,"DL":0},
        "L": {"UF":0,"UR":0,"UB":0,"UL":0,"FR":0,"RB":0,"BL":0,"LF":0,
              "DF":0,"DR":0,"DB":0,"DL":0},
        "F": {"UF":1,"UR":0,"UB":0,"UL":0,"FR":1,"RB":0,"BL":0,"LF":1,
              "DF":1,"DR":0,"DB":0,"DL":0},
        "B": {"UF":0,"UR":0,"UB":1,"UL":0,"FR":0,"RB":1,"BL":1,"LF":0,
              "DF":0,"DR":0,"DB":1,"DL":0},
    }
    try:
        return deltas[face][piece_name]
    except KeyError as exc:
        raise ValueError(
            f"Invalid edge orientation lookup: piece={piece_name}, face={face}"
        ) from exc


# ============================================================================
# CubieState - transform one corner
# ============================================================================

def _transform_corner(position_index: int, corner: CornerCubie, face: str) -> tuple[int, CornerCubie]:
    # Use the CURRENT position slot name for both geometry and orientation delta.
    # Orientation twist is a property of which slot is turning, not which piece
    # identity is sitting there.
    current_slot_name = CORNER_NAMES[position_index]
    current_position = _piece_position(current_slot_name)
    face_normal = FACE_BASIS[face][0]

    if _dot(current_position, face_normal) != 1:
        return position_index, corner.copy()

    new_position = _rotate_clockwise(current_position, face_normal)
    destination_position = CORNER_POSITION_LOOKUP.get(new_position)
    if destination_position is None:
        raise RuntimeError(
            "Corner destination could not be determined.\n"
            f"Slot: {current_slot_name}\nMove: {face}\nPosition: {new_position}"
        )

    orientation = (
        corner.orientation + _corner_orientation_delta(current_slot_name, face)
    ) % 3

    return destination_position, CornerCubie(
        piece=corner.piece,
        orientation=orientation,
    )


# ============================================================================
# CubieState - transform one edge
# ============================================================================

def _transform_edge(position_index: int, edge: EdgeCubie, face: str) -> tuple[int, EdgeCubie]:
    # Use the CURRENT position slot name for both geometry and orientation delta.
    current_slot_name = EDGE_NAMES[position_index]
    current_position = _piece_position(current_slot_name)
    face_normal = FACE_BASIS[face][0]

    if _dot(current_position, face_normal) != 1:
        return position_index, edge.copy()

    new_position = _rotate_clockwise(current_position, face_normal)
    destination_position = EDGE_POSITION_LOOKUP.get(new_position)
    if destination_position is None:
        raise RuntimeError(
            "Edge destination could not be determined.\n"
            f"Slot: {current_slot_name}\nMove: {face}\nPosition: {new_position}"
        )

    orientation = (
        edge.orientation + _edge_orientation_delta(current_slot_name, face)
    ) % 2

    return destination_position, EdgeCubie(
        piece=edge.piece,
        orientation=orientation,
    )


# ============================================================================
# CubieState - single clockwise quarter turn
# ============================================================================

def _apply_clockwise_quarter_turn_cubie(
    cube: CubieState,
    face: str,
) -> None:
    """
    Apply one clockwise quarter turn directly to CubieState.

    The transformation is derived from the same physical 3D
    geometry used by the sticker move engine.

    This updates:

        - corner permutation
        - corner orientation
        - edge permutation
        - edge orientation
    """

    if CubieState is None:
        raise RuntimeError(
            "CubieState could not be imported: "
            f"{CUBIE_IMPORT_ERROR}"
        )

    face = face.upper()

    if face not in VALID_FACES:
        raise ValueError(
            f"Invalid face: {face}"
        )

    original_corners = [
        corner.copy()
        for corner in cube.corners
    ]

    original_edges = [
        edge.copy()
        for edge in cube.edges
    ]

    updated_corners = [
        None
        for _ in range(8)
    ]

    updated_edges = [
        None
        for _ in range(12)
    ]

    for position_index, corner in enumerate(
        original_corners
    ):

        destination, transformed = (
            _transform_corner(
                position_index,
                corner,
                face,
            )
        )

        updated_corners[
            destination
        ] = transformed

    for position_index, edge in enumerate(
        original_edges
    ):

        destination, transformed = (
            _transform_edge(
                position_index,
                edge,
                face,
            )
        )

        updated_edges[
            destination
        ] = transformed

    if any(
        corner is None
        for corner in updated_corners
    ):
        raise RuntimeError(
            f"Corner transformation incomplete for {face}."
        )

    if any(
        edge is None
        for edge in updated_edges
    ):
        raise RuntimeError(
            f"Edge transformation incomplete for {face}."
        )

    cube.corners = updated_corners
    cube.edges = updated_edges

    validation = cube.validate()

    if not validation["valid"]:
        raise RuntimeError(
            "Cubie move produced an invalid cube.\n"
            f"Move: {face}\n"
            f"Errors: {validation['errors']}"
        )


# ============================================================================
# CubieState - apply move
# ============================================================================

def apply_move_cubie(
    cube: CubieState,
    move: Move,
) -> CubieState:
    """
    Apply one move to a CubieState.

    The original CubieState is never modified.
    """

    if CubieState is None:
        raise RuntimeError(
            "CubieState could not be imported: "
            f"{CUBIE_IMPORT_ERROR}"
        )

    if not isinstance(cube, CubieState):
        raise TypeError(
            "cube must be a CubieState."
        )

    if not isinstance(move, Move):
        raise TypeError(
            "move must be a Move."
        )

    result = cube.copy()

    for _ in range(
        move.quarter_turns
    ):

        _apply_clockwise_quarter_turn_cubie(
            result,
            move.face,
        )

    return result


# ============================================================================
# CubieState - apply multiple moves
# ============================================================================

def apply_moves_cubie(
    cube: CubieState,
    moves: Iterable[Move],
) -> CubieState:

    result = cube

    for move in moves:

        result = apply_move_cubie(
            result,
            move,
        )

    return result


# ============================================================================
# CubieState - apply algorithm
# ============================================================================

def apply_algorithm_cubie(
    cube: CubieState,
    algorithm: str,
) -> CubieState:

    return apply_moves_cubie(
        cube,
        parse_algorithm(algorithm),
    )


def apply_scramble_cubie(
    cube: CubieState,
    scramble: str,
) -> CubieState:

    return apply_algorithm_cubie(
        cube,
        scramble,
    )


# ============================================================================
# Solved CubeState
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
# Solved CubieState
# ============================================================================

def _create_solved_cubie() -> CubieState:

    if CubieState is None:
        raise RuntimeError(
            "CubieState could not be imported: "
            f"{CUBIE_IMPORT_ERROR}"
        )

    return CubieState()


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


def _cubie_states_equal(
    first: CubieState,
    second: CubieState,
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
# Basic CubeState inverse tests
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
# CubeState four-turn tests
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
# CubeState algorithm inverse test
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
# CubeState immutability
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
# CubieState basic inverse tests
# ============================================================================

def _test_cubie_basic_inverses(
    cube: CubieState,
) -> bool:

    print(
        "CubieState inverse tests:"
    )

    all_passed = True

    for face in FACE_NAMES:

        algorithm = (
            f"{face} {face}'"
        )

        restored = apply_algorithm_cubie(
            cube,
            algorithm,
        )

        passed = _cubie_states_equal(
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
        "CubieState inverse tests:",
        "PASS" if all_passed else "FAILED",
    )

    return all_passed


# ============================================================================
# CubieState four-turn tests
# ============================================================================

def _test_cubie_four_turns(
    cube: CubieState,
) -> bool:

    print(
        "CubieState four-turn tests:"
    )

    all_passed = True

    for face in FACE_NAMES:

        algorithm = (
            f"{face} "
            f"{face} "
            f"{face} "
            f"{face}"
        )

        restored = apply_algorithm_cubie(
            cube,
            algorithm,
        )

        passed = _cubie_states_equal(
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
        "CubieState four-turn tests:",
        "PASS" if all_passed else "FAILED",
    )

    return all_passed


# ============================================================================
# CubieState algorithm inverse test
# ============================================================================

def _test_cubie_algorithm_inverse(
    cube: CubieState,
) -> bool:

    algorithm = (
        "R U R' U' F2 L D"
    )

    inverse = invert_algorithm(
        algorithm
    )

    scrambled = apply_algorithm_cubie(
        cube,
        algorithm,
    )

    restored = apply_algorithm_cubie(
        scrambled,
        inverse,
    )

    passed = _cubie_states_equal(
        restored,
        cube,
    )

    print(
        "Cubie algorithm:",
        algorithm,
    )

    print(
        "Cubie inverse:",
        inverse,
    )

    print(
        "Cubie algorithm + inverse restores cube:",
        passed,
    )

    return passed


# ============================================================================
# CubieState physical validation tests
# ============================================================================

def _test_cubie_validation(
    cube: CubieState,
) -> bool:

    print(
        "CubieState validation tests:"
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

        moved = apply_algorithm_cubie(
            cube,
            algorithm,
        )

        validation = moved.validate()

        passed = validation["valid"]

        print(
            f"  {algorithm}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:

            for error in validation["errors"]:

                print(
                    f"    - {error}"
                )

            all_passed = False

    print()

    print(
        "CubieState validation:",
        "PASS" if all_passed else "FAILED",
    )

    return all_passed


# ============================================================================
# CubieState immutability
# ============================================================================

def _test_cubie_original_unchanged(
    cube: CubieState,
) -> bool:

    original = _create_solved_cubie()

    moved = apply_algorithm_cubie(
        original,
        "R U F D L B",
    )

    original_unchanged = _cubie_states_equal(
        original,
        cube,
    )

    moved_differs = not _cubie_states_equal(
        moved,
        cube,
    )

    print(
        "Original CubieState unchanged:",
        original_unchanged,
    )

    print(
        "Returned CubieState differs:",
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
    # CubeState
    # ------------------------------------------------------------------------

    cube = _create_solved_cube()

    print(
        "Solved cube color counts:"
    )

    print(
        cube.color_counts()
    )

    print()

    basic_passed = _test_basic_inverses(
        cube
    )

    print()

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

    four_turn_passed = _test_four_turns(
        cube
    )

    print()

    algorithm_inverse_passed = (
        _test_algorithm_inverse(
            cube
        )
    )

    print()

    validator_passed = (
        _test_validator_integration(
            cube
        )
    )

    print()

    unchanged_passed = (
        _test_original_unchanged(
            cube
        )
    )

    print()

    # ------------------------------------------------------------------------
    # CubieState
    # ------------------------------------------------------------------------

    print(
        "========================================"
    )

    print(
        "CubieState Move Engine"
    )

    print(
        "========================================"
    )

    print()

    cubie = _create_solved_cubie()

    print(
        "Solved CubieState:"
    )

    print(
        cubie
    )

    print()

    print(
        f"Solved: {cubie.is_solved()}"
    )

    print(
        f"Validation: {cubie.validate()['valid']}"
    )

    print()

    cubie_inverse_passed = (
        _test_cubie_basic_inverses(
            cubie
        )
    )

    print()

    cubie_four_turn_passed = (
        _test_cubie_four_turns(
            cubie
        )
    )

    print()

    cubie_algorithm_inverse_passed = (
        _test_cubie_algorithm_inverse(
            cubie
        )
    )

    print()

    cubie_validation_passed = (
        _test_cubie_validation(
            cubie
        )
    )

    print()

    cubie_unchanged_passed = (
        _test_cubie_original_unchanged(
            cubie
        )
    )

    print()

    # ------------------------------------------------------------------------
    # Example CubieState scramble
    # ------------------------------------------------------------------------

    scramble = (
        "R U R' U'"
    )

    scrambled_cubie = apply_algorithm_cubie(
        cubie,
        scramble,
    )

    print(
        "Example CubieState scramble:"
    )

    print(
        f"  Algorithm: {scramble}"
    )

    print()

    print(
        scrambled_cubie
    )

    print()

    print(
        "Validation:"
    )

    validation = scrambled_cubie.validate()

    print(
        f"  Valid: {validation['valid']}"
    )

    if validation["errors"]:

        for error in validation["errors"]:

            print(
                f"  - {error}"
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
        and cubie_inverse_passed
        and cubie_four_turn_passed
        and cubie_algorithm_inverse_passed
        and cubie_validation_passed
        and cubie_unchanged_passed
    )

    print(
        "========================================"
    )

    if all_passed:

        print(
            "Move engine tests PASSED."
        )

        print(
            "CubeState engine: PASS"
        )

        print(
            "CubieState engine: PASS"
        )

    else:

        print(
            "Move engine tests FAILED."
        )

    print(
        "========================================"
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()