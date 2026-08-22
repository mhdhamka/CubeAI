"""
CubeAI - Cubie Converter

Converts between:

    CubeState  - sticker/face representation
    CubieState - physical piece representation

Conventions are taken directly from cubeValidator.py and move.py
so there is one source of truth and no second implementation that
can drift.

Color scheme (from cubeValidator.py):

    U = white
    R = red
    F = green
    D = yellow
    L = orange
    B = blue

Corner slot order (from cubeValidator.py CORNER_FACELETS):

    0  UFR
    1  URB
    2  UBL
    3  ULF
    4  DFR
    5  DRB
    6  DBL
    7  DLF

Edge slot order (from cubeValidator.py EDGE_FACELETS):

    0   UF
    1   UR
    2   UB
    3   UL
    4   FR
    5   BR   (move.py calls this RB)
    6   BL
    7   FL   (move.py calls this LF)
    8   DF
    9   DR
    10  DB
    11  DL

Pipeline:

    Scanner
        |
        v
    CubeState
        |
        v
    CubieConverter   <-- this module
        |
        v
    CubieState
        |
        v
    Solver
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any, Optional

# ============================================================================
# Paths
# ============================================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


# ============================================================================
# Imports
#
# TYPE_CHECKING is False at runtime, so the block below is only read by
# Pylance / mypy, giving the type-checker the real class types.
# At runtime we import into private _-prefixed names and expose them
# through the module so call-sites never reference None as a type.
# ============================================================================

if TYPE_CHECKING:
    from cubeState import CubeState
    from cubie import CubieState, CornerCubie, EdgeCubie
    from cubeValidator import CubeValidator

# ---- runtime imports -------------------------------------------------------

_CubeState: Any = None
_CubieState: Any = None
_CornerCubie: Any = None
_EdgeCubie: Any = None
_CubeValidator: Any = None

CUBE_STATE_IMPORT_ERROR: Optional[str] = None
CUBIE_IMPORT_ERROR: Optional[str] = None
CUBE_VALIDATOR_IMPORT_ERROR: Optional[str] = None

try:
    from cubeState import CubeState as _CubeState  # type: ignore[no-redef]
except ImportError as _exc:
    CUBE_STATE_IMPORT_ERROR = str(_exc)

try:
    from cubie import (  # type: ignore[no-redef]
        CubieState as _CubieState,
        CornerCubie as _CornerCubie,
        EdgeCubie as _EdgeCubie,
    )
except ImportError as _exc:
    CUBIE_IMPORT_ERROR = str(_exc)

try:
    from cubeValidator import (  # type: ignore[no-redef]
        CubeValidator as _CubeValidator,
        CORNER_FACELETS as _CORNER_FACELETS,
        EDGE_FACELETS as _EDGE_FACELETS,
        CORNER_COLORS as _CORNER_COLORS,
        EDGE_COLORS as _EDGE_COLORS,
    )
    CORNER_FACELETS = _CORNER_FACELETS
    EDGE_FACELETS = _EDGE_FACELETS
    CORNER_COLORS = _CORNER_COLORS
    EDGE_COLORS = _EDGE_COLORS
except ImportError as _exc:
    CUBE_VALIDATOR_IMPORT_ERROR = str(_exc)
    CORNER_FACELETS = None
    EDGE_FACELETS = None
    CORNER_COLORS = None
    EDGE_COLORS = None


# ============================================================================
# Color / face mappings  (must match cubeValidator.py EXPECTED_CENTERS)
# ============================================================================

FACE_TO_COLOR: dict[str, str] = {
    "U": "white",
    "R": "red",
    "F": "green",
    "D": "yellow",
    "L": "orange",
    "B": "blue",
}

COLOR_TO_FACE: dict[str, str] = {v: k for k, v in FACE_TO_COLOR.items()}

FACE_NAMES: tuple[str, ...] = ("U", "R", "F", "D", "L", "B")

VALID_COLORS: frozenset[str] = frozenset(FACE_TO_COLOR.values())


# ============================================================================
# Canonical corner color tuples
#
# Each tuple lists the three sticker colors in the same order as the
# corresponding CORNER_FACELETS entry so that orientation 0 maps
# canonical[i] directly to facelet[i].
#
#   0  UFR  facelets: U, F, R  -> white, green, red
#   1  URB  facelets: U, R, B  -> white, red,   blue
#   2  UBL  facelets: U, B, L  -> white, blue,  orange
#   3  ULF  facelets: U, L, F  -> white, orange,green
#   4  DFR  facelets: D, F, R  -> yellow,green, red
#   5  DRB  facelets: D, R, B  -> yellow,red,   blue
#   6  DBL  facelets: D, B, L  -> yellow,blue,  orange
#   7  DLF  facelets: D, L, F  -> yellow,orange,green
# ============================================================================

CORNER_CANONICAL: tuple[tuple[str, str, str], ...] = (
    ("white",  "green",  "red"),      # 0  UFR
    ("white",  "red",    "blue"),     # 1  URB
    ("white",  "blue",   "orange"),   # 2  UBL
    ("white",  "orange", "green"),    # 3  ULF
    ("yellow", "green",  "red"),      # 4  DFR
    ("yellow", "red",    "blue"),     # 5  DRB
    ("yellow", "blue",   "orange"),   # 6  DBL
    ("yellow", "orange", "green"),    # 7  DLF
)


# ============================================================================
# Canonical edge color tuples
#
# Each tuple lists the two sticker colors in the same order as the
# corresponding EDGE_FACELETS entry so that orientation 0 maps
# canonical[i] directly to facelet[i].
#
#   0  UF  facelets: U, F  -> white,  green
#   1  UR  facelets: U, R  -> white,  red
#   2  UB  facelets: U, B  -> white,  blue
#   3  UL  facelets: U, L  -> white,  orange
#   4  FR  facelets: F, R  -> green,  red
#   5  BR  facelets: B, R  -> blue,   red
#   6  BL  facelets: B, L  -> blue,   orange
#   7  FL  facelets: F, L  -> green,  orange
#   8  DF  facelets: D, F  -> yellow, green
#   9  DR  facelets: D, R  -> yellow, red
#   10 DB  facelets: D, B  -> yellow, blue
#   11 DL  facelets: D, L  -> yellow, orange
# ============================================================================

EDGE_CANONICAL: tuple[tuple[str, str], ...] = (
    ("white",  "green"),    # 0  UF
    ("white",  "red"),      # 1  UR
    ("white",  "blue"),     # 2  UB
    ("white",  "orange"),   # 3  UL
    ("green",  "red"),      # 4  FR
    ("blue",   "red"),      # 5  BR
    ("blue",   "orange"),   # 6  BL
    ("green",  "orange"),   # 7  FL
    ("yellow", "green"),    # 8  DF
    ("yellow", "red"),      # 9  DR
    ("yellow", "blue"),     # 10 DB
    ("yellow", "orange"),   # 11 DL
)


# ============================================================================
# Import guard
# ============================================================================

def _require_imports() -> None:
    """Raise a clear RuntimeError if any required module failed to import."""

    if _CubeState is None:
        raise RuntimeError(
            "CubeState could not be imported: "
            f"{CUBE_STATE_IMPORT_ERROR}"
        )

    if _CubieState is None:
        raise RuntimeError(
            "CubieState could not be imported: "
            f"{CUBIE_IMPORT_ERROR}"
        )

    if _CubeValidator is None:
        raise RuntimeError(
            "CubeValidator could not be imported: "
            f"{CUBE_VALIDATOR_IMPORT_ERROR}"
        )


# ============================================================================
# Orientation helpers  (mirror cubeValidator.py exactly)
# ============================================================================

def _corner_orientation(
    colors: list[str],
    facelets: Any,
) -> int:
    """
    Mirror of CubeValidator._corner_orientation().

    Returns:
        0 = correctly oriented
        1 = clockwise twist
        2 = counter-clockwise twist
    """

    ud_index = -1

    for index, color in enumerate(colors):
        if color in ("white", "yellow"):
            ud_index = index
            break

    if ud_index == -1:
        return 0

    # U-layer: orientation == position of white/yellow in color list.
    if facelets[0][0] == "U":
        return ud_index

    # D-layer: opposite handedness.
    return (-ud_index) % 3


def _edge_orientation(
    colors: list[str],
    facelets: Any,
) -> int:
    """
    Mirror of CubeValidator._edge_orientation().

    Returns:
        0 = correctly oriented
        1 = flipped
    """

    faces = (facelets[0][0], facelets[1][0])

    if "white" in colors or "yellow" in colors:
        target = "white" if "white" in colors else "yellow"
        for color, face in zip(colors, faces):
            if color == target and face in ("U", "D"):
                return 0
        return 1

    if "green" in colors or "blue" in colors:
        target = "green" if "green" in colors else "blue"
        for color, face in zip(colors, faces):
            if color == target and face in ("F", "B"):
                return 0
        return 1

    return 1


# ============================================================================
# CubeState → CubieState
# ============================================================================

def cubestate_to_cubiestate(cube: "CubeState") -> "CubieState":
    """
    Convert a CubeState to a CubieState.

    Steps:

        1. Read the three sticker colors at each corner slot.
        2. Identify which corner piece is there (by color set).
        3. Compute corner orientation using the same rule as
           cubeValidator._corner_orientation().
        4. Repeat for all twelve edge slots.
        5. Assemble and return a CubieState.

    Raises:
        RuntimeError  if any import failed or the cube is invalid.
        ValueError    if a cubie cannot be identified.
    """

    _require_imports()

    corners = []

    for slot_index, facelets in enumerate(CORNER_FACELETS):

        colors = [
            str(cube.faces[face][row][col]).lower()
            for face, row, col in facelets
        ]

        color_set = frozenset(colors)

        if color_set not in CORNER_COLORS:
            raise ValueError(
                f"Unrecognised corner at slot {slot_index}: {colors}"
            )

        piece_index = CORNER_COLORS.index(color_set)
        orientation = _corner_orientation(colors, facelets)

        corners.append(
            _CornerCubie(piece=piece_index, orientation=orientation)
        )

    edges = []

    for slot_index, facelets in enumerate(EDGE_FACELETS):

        colors = [
            str(cube.faces[face][row][col]).lower()
            for face, row, col in facelets
        ]

        color_set = frozenset(colors)

        if color_set not in EDGE_COLORS:
            raise ValueError(
                f"Unrecognised edge at slot {slot_index}: {colors}"
            )

        piece_index = EDGE_COLORS.index(color_set)
        orientation = _edge_orientation(colors, facelets)

        edges.append(
            _EdgeCubie(piece=piece_index, orientation=orientation)
        )

    return _CubieState(corners=corners, edges=edges)


# ============================================================================
# CubieState → CubeState
# ============================================================================

def cubiestate_to_cubestate(cubie: "CubieState") -> "CubeState":
    """
    Convert a CubieState to a CubeState.

    Steps:

        1. Build a blank 6-face grid.
        2. Fill in the six center stickers (they are fixed).
        3. For each corner slot, look up which piece is there,
           rotate its canonical color tuple by the stored orientation,
           and write each sticker to the correct facelet position.
        4. Repeat for all twelve edge slots.
        5. Return the assembled CubeState.

    Raises:
        RuntimeError  if any import failed.
        ValueError    if orientation values are out of range.

    Corner rotation rule
    --------------------
    _corner_orientation() returns ud_index = the index in the colors list
    where white/yellow sits.  CORNER_CANONICAL[piece][0] IS always the
    white/yellow color.  To reconstruct we need canonical[0] to land at
    position ud_index, so:

        rotated[0] = canonical[(-ud_index) % 3]   (shift left by ud_index)
        rotated[1] = canonical[(-ud_index + 1) % 3]
        rotated[2] = canonical[(-ud_index + 2) % 3]

    For U-layer slots:  ud_index == orientation
    For D-layer slots:  orientation = (-ud_index) % 3
                        => ud_index = (-orientation) % 3
    """

    _require_imports()

    # Start with a blank grid.
    faces: dict[str, list[list[str]]] = {
        face: [[""] * 3 for _ in range(3)]
        for face in FACE_NAMES
    }

    # Fill centers (fixed).
    for face, color in FACE_TO_COLOR.items():
        faces[face][1][1] = color

    # -------------------------------------------------------------------------
    # Corners
    # -------------------------------------------------------------------------

    for slot_index, facelets in enumerate(CORNER_FACELETS):

        corner = cubie.corners[slot_index]
        piece_index: int = corner.piece
        orientation: int = corner.orientation

        if orientation not in (0, 1, 2):
            raise ValueError(
                f"Corner slot {slot_index}: invalid orientation {orientation}"
            )

        canonical = CORNER_CANONICAL[piece_index]

        is_d_layer = (facelets[0][0] == "D")

        # Recover ud_index from orientation.
        ud_index = (-orientation) % 3 if is_d_layer else orientation

        # Shift the canonical tuple left by ud_index so canonical[0]
        # (white/yellow) lands at position ud_index.
        rotated = (
            canonical[(-ud_index) % 3],
            canonical[(-ud_index + 1) % 3],
            canonical[(-ud_index + 2) % 3],
        )

        for (face, row, col), color in zip(facelets, rotated):
            faces[face][row][col] = color

    # -------------------------------------------------------------------------
    # Edges
    # -------------------------------------------------------------------------

    for slot_index, facelets in enumerate(EDGE_FACELETS):

        edge = cubie.edges[slot_index]
        piece_index = edge.piece
        orientation = edge.orientation

        if orientation not in (0, 1):
            raise ValueError(
                f"Edge slot {slot_index}: invalid orientation {orientation}"
            )

        canonical_edge = EDGE_CANONICAL[piece_index]

        # orientation 0 -> canonical order; orientation 1 -> swapped
        rotated_edge = (
            canonical_edge[orientation % 2],
            canonical_edge[(orientation + 1) % 2],
        )

        for (face, row, col), color in zip(facelets, rotated_edge):
            faces[face][row][col] = color

    return _CubeState(faces)


# ============================================================================
# Test helpers
# ============================================================================

def _create_solved_cubestate() -> "CubeState":

    if _CubeState is None:
        raise RuntimeError(CUBE_STATE_IMPORT_ERROR)

    faces: dict[str, list[list[str]]] = {}

    for face, color in FACE_TO_COLOR.items():
        faces[face] = [
            [color, color, color],
            [color, color, color],
            [color, color, color],
        ]

    return _CubeState(faces)


def _create_solved_cubiestate() -> "CubieState":

    if _CubieState is None:
        raise RuntimeError(CUBIE_IMPORT_ERROR)

    corners = [_CornerCubie(piece=i, orientation=0) for i in range(8)]
    edges = [_EdgeCubie(piece=i, orientation=0) for i in range(12)]

    return _CubieState(corners=corners, edges=edges)


def _cubiestate_equal(a: "CubieState", b: "CubieState") -> bool:

    for i in range(8):
        if a.corners[i].piece != b.corners[i].piece:
            return False
        if a.corners[i].orientation != b.corners[i].orientation:
            return False

    for i in range(12):
        if a.edges[i].piece != b.edges[i].piece:
            return False
        if a.edges[i].orientation != b.edges[i].orientation:
            return False

    return True


def _cubestate_equal(a: "CubeState", b: "CubeState") -> bool:

    for face in FACE_NAMES:
        for row in range(3):
            for col in range(3):
                if a.faces[face][row][col] != b.faces[face][row][col]:
                    return False

    return True


# ============================================================================
# Tests
# ============================================================================

def _test_solved_cubestate_to_cubiestate() -> bool:

    cube = _create_solved_cubestate()
    cubie = cubestate_to_cubiestate(cube)
    solved = _create_solved_cubiestate()
    passed = _cubiestate_equal(cubie, solved)

    print(
        "  Solved CubeState -> CubieState:",
        "PASS" if passed else "FAIL",
    )

    return passed


def _test_solved_cubiestate_to_cubestate() -> bool:

    cubie = _create_solved_cubiestate()
    cube = cubiestate_to_cubestate(cubie)
    solved = _create_solved_cubestate()
    passed = _cubestate_equal(cube, solved)

    print(
        "  Solved CubieState -> CubeState:",
        "PASS" if passed else "FAIL",
    )

    return passed


def _test_round_trips() -> bool:

    try:
        from move import apply_algorithm, apply_algorithm_cubie  # noqa: F401
    except ImportError as exc:
        print(f"  Round-trip tests skipped: {exc}")
        return True

    algorithms = (
        "R", "U", "F", "D", "L", "B",
        "R U R' U'",
        "R U R' U' F2 L D",
        "R U R' U' F2 L D B R2 U2",
        "F R U R' U' F'",
        "R2 U2 F2 D2 L2 B2",
    )

    solved_cube = _create_solved_cubestate()
    all_passed = True

    print("  Round-trip tests (CubeState -> CubieState -> CubeState):")

    for algorithm in algorithms:

        try:
            from move import apply_algorithm as _apply_alg
            scrambled_cube = _apply_alg(solved_cube, algorithm)
            converted_cubie = cubestate_to_cubiestate(scrambled_cube)
            restored_cube = cubiestate_to_cubestate(converted_cubie)
            passed = _cubestate_equal(scrambled_cube, restored_cube)

        except Exception as exc:
            print(f"    {algorithm}: FAIL ({exc})")
            all_passed = False
            continue

        print(f"    {algorithm}:", "PASS" if passed else "FAIL")

        if not passed:
            all_passed = False

    return all_passed


def _test_consistency() -> bool:

    try:
        from move import apply_algorithm, apply_algorithm_cubie  # noqa: F401
    except ImportError as exc:
        print(f"  Consistency tests skipped: {exc}")
        return True

    algorithms = (
        "R", "U", "F", "D", "L", "B",
        "R U R' U'",
        "R U R' U' F2 L D",
        "R U R' U' F2 L D B R2 U2",
        "F R U R' U' F'",
        "R2 U2 F2 D2 L2 B2",
    )

    solved_cube = _create_solved_cubestate()
    solved_cubie = _create_solved_cubiestate()
    all_passed = True

    print(
        "  Consistency tests "
        "(CubeState move == CubieState move via converter):"
    )

    for algorithm in algorithms:

        try:
            from move import apply_algorithm as _apply_alg
            from move import apply_algorithm_cubie as _apply_alg_cubie

            moved_cube = _apply_alg(solved_cube, algorithm)
            cubie_via_cube = cubestate_to_cubiestate(moved_cube)
            cubie_direct = _apply_alg_cubie(solved_cubie, algorithm)
            passed = _cubiestate_equal(cubie_via_cube, cubie_direct)

        except Exception as exc:
            print(f"    {algorithm}: FAIL ({exc})")
            all_passed = False
            continue

        print(f"    {algorithm}:", "PASS" if passed else "FAIL")

        if not passed:
            all_passed = False

    return all_passed


def _test_immutability() -> bool:

    cube_original = _create_solved_cubestate()
    cubie_original = _create_solved_cubiestate()
    cube_snapshot = _create_solved_cubestate()
    cubie_snapshot = _create_solved_cubiestate()

    cubestate_to_cubiestate(cube_original)
    cubiestate_to_cubestate(cubie_original)

    cube_unchanged = _cubestate_equal(cube_original, cube_snapshot)
    cubie_unchanged = _cubiestate_equal(cubie_original, cubie_snapshot)

    print("  CubeState unchanged after conversion:", cube_unchanged)
    print("  CubieState unchanged after conversion:", cubie_unchanged)

    return cube_unchanged and cubie_unchanged


# ============================================================================
# Main
# ============================================================================

def main() -> None:

    print("=" * 40)
    print("CubeAI Cubie Converter")
    print("=" * 40)
    print()

    all_passed = True

    print("Solved-state tests:")
    if not _test_solved_cubestate_to_cubiestate():
        all_passed = False
    if not _test_solved_cubiestate_to_cubestate():
        all_passed = False
    print()

    if not _test_round_trips():
        all_passed = False
    print()

    if not _test_consistency():
        all_passed = False
    print()

    print("Immutability tests:")
    if not _test_immutability():
        all_passed = False
    print()

    print("=" * 40)
    print("Converter tests:", "PASSED" if all_passed else "FAILED")
    print("=" * 40)


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()
