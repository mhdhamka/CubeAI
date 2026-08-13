
"""
CubeAI - Cube State Validator

Validates whether a CubeState represents a physically possible
Rubik's Cube configuration.

The validator checks:

1. Cube structure
2. Valid face names
3. Valid colors
4. Exactly 9 stickers of each color
5. Unique center colors
6. Standard center color scheme
7. Valid corner cubies
8. Valid edge cubies
9. Corner orientation
10. Edge orientation
11. Corner permutation parity
12. Edge permutation parity

Expected color scheme:

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

Each face is represented as:

    0 1 2
    3 4 5
    6 7 8

This module does NOT solve the cube.

Pipeline:

    Scanner
        |
        v
    CubeState
        |
        v
    CubeValidator
        |
        v
    Solver
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any


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

EXPECTED_FACE_COUNT = 6
EXPECTED_STICKER_COUNT = 54
EXPECTED_COLOR_COUNT = 9

FACE_NAMES = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)

VALID_COLORS = {
    "white",
    "yellow",
    "red",
    "orange",
    "green",
    "blue",
}


# Standard CubeAI color scheme.

EXPECTED_CENTERS = {
    "U": "white",
    "R": "red",
    "F": "green",
    "D": "yellow",
    "L": "orange",
    "B": "blue",
}


# ============================================================================
# Cubie definitions
# ============================================================================

# Corners:
#
# UFR
# URB
# UBL
# ULF
# DFR
# DRB
# DBL
# DLF
#
# The order of the facelets is important.
#
# The four U-layer corner definitions use one handedness.
# The four D-layer corner definitions use the opposite handedness.
#
# _corner_orientation() compensates for this so that all eight
# corner positions use one consistent orientation convention.

CORNER_FACELETS = (
    (
        ("U", 2, 2),
        ("F", 0, 2),
        ("R", 0, 0),
    ),
    (
        ("U", 0, 2),
        ("R", 0, 2),
        ("B", 0, 0),
    ),
    (
        ("U", 0, 0),
        ("B", 0, 2),
        ("L", 0, 0),
    ),
    (
        ("U", 2, 0),
        ("L", 0, 2),
        ("F", 0, 0),
    ),
    (
        ("D", 0, 2),
        ("F", 2, 2),
        ("R", 2, 0),
    ),
    (
        ("D", 2, 2),
        ("R", 2, 2),
        ("B", 2, 0),
    ),
    (
        ("D", 2, 0),
        ("B", 2, 2),
        ("L", 2, 0),
    ),
    (
        ("D", 0, 0),
        ("L", 2, 2),
        ("F", 2, 0),
    ),
)


# Edges:
#
# UF
# UR
# UB
# UL
# FR
# BR
# BL
# FL
# DF
# DR
# DB
# DL

EDGE_FACELETS = (
    (
        ("U", 2, 1),
        ("F", 0, 1),
    ),
    (
        ("U", 1, 2),
        ("R", 0, 1),
    ),
    (
        ("U", 0, 1),
        ("B", 0, 1),
    ),
    (
        ("U", 1, 0),
        ("L", 0, 1),
    ),
    (
        ("F", 1, 2),
        ("R", 1, 0),
    ),
    (
        ("B", 1, 0),
        ("R", 1, 2),
    ),
    (
        ("B", 1, 2),
        ("L", 1, 0),
    ),
    (
        ("F", 1, 0),
        ("L", 1, 2),
    ),
    (
        ("D", 0, 1),
        ("F", 2, 1),
    ),
    (
        ("D", 1, 2),
        ("R", 2, 1),
    ),
    (
        ("D", 2, 1),
        ("B", 2, 1),
    ),
    (
        ("D", 1, 0),
        ("L", 2, 1),
    ),
)


# ============================================================================
# Canonical cubie colors
# ============================================================================

CORNER_COLORS = (
    frozenset(("white", "green", "red")),       # UFR
    frozenset(("white", "red", "blue")),        # URB
    frozenset(("white", "blue", "orange")),     # UBL
    frozenset(("white", "orange", "green")),    # ULF
    frozenset(("yellow", "green", "red")),      # DFR
    frozenset(("yellow", "red", "blue")),       # DRB
    frozenset(("yellow", "blue", "orange")),    # DBL
    frozenset(("yellow", "orange", "green")),   # DLF
)

EDGE_COLORS = (
    frozenset(("white", "green")),       # UF
    frozenset(("white", "red")),         # UR
    frozenset(("white", "blue")),        # UB
    frozenset(("white", "orange")),      # UL
    frozenset(("green", "red")),         # FR
    frozenset(("blue", "red")),          # BR
    frozenset(("blue", "orange")),       # BL
    frozenset(("green", "orange")),      # FL
    frozenset(("yellow", "green")),      # DF
    frozenset(("yellow", "red")),        # DR
    frozenset(("yellow", "blue")),       # DB
    frozenset(("yellow", "orange")),     # DL
)


# ============================================================================
# Validation result
# ============================================================================

@dataclass
class ValidationResult:
    """
    Result of cube validation.
    """

    valid: bool

    errors: list[str]

    warnings: list[str]

    sticker_count: int = 0

    color_counts: dict[str, int] | None = None

    corner_orientation_sum: int = 0

    edge_orientation_sum: int = 0

    corner_permutation_parity: int = 0

    edge_permutation_parity: int = 0

    def to_dict(self) -> dict[str, Any]:
        """
        Convert validation result to a JSON-compatible dictionary.
        """

        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "sticker_count": self.sticker_count,
            "color_counts": self.color_counts or {},
            "corner_orientation_sum": (
                self.corner_orientation_sum
            ),
            "edge_orientation_sum": (
                self.edge_orientation_sum
            ),
            "corner_permutation_parity": (
                self.corner_permutation_parity
            ),
            "edge_permutation_parity": (
                self.edge_permutation_parity
            ),
        }


# ============================================================================
# Cube Validator
# ============================================================================

class CubeValidator:
    """
    Validates CubeState objects.

    The validator is intentionally independent from:

        - Scanner
        - Scramble engine
        - Solver

    It only answers:

        "Is this cube state physically valid?"
    """

    def validate(
        self,
        cube: CubeState,
    ) -> ValidationResult:
        """
        Validate a CubeState.

        Returns:
            ValidationResult
        """

        errors: list[str] = []
        warnings: list[str] = []

        if CubeState is None:
            return ValidationResult(
                valid=False,
                errors=[
                    "CubeState could not be imported: "
                    f"{CUBE_STATE_IMPORT_ERROR}"
                ],
                warnings=[],
            )

        if not isinstance(cube, CubeState):
            return ValidationResult(
                valid=False,
                errors=[
                    "cube must be a CubeState."
                ],
                warnings=[],
            )

        # ====================================================================
        # Structural validation
        # ====================================================================

        structure_errors = self._validate_structure(cube)

        errors.extend(structure_errors)

        if errors:
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
            )

        # ====================================================================
        # Flatten stickers
        # ====================================================================

        stickers = self._flatten_cube(cube)

        sticker_count = len(stickers)

        # ====================================================================
        # Color validation
        # ====================================================================

        color_counts = self._count_colors(stickers)

        errors.extend(
            self._validate_colors(
                stickers,
                color_counts,
            )
        )

        # ====================================================================
        # Center validation
        # ====================================================================

        errors.extend(
            self._validate_centers(cube)
        )

        if errors:
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                sticker_count=sticker_count,
                color_counts=color_counts,
            )

        # ====================================================================
        # Corner validation
        # ====================================================================

        (
            corner_errors,
            corner_orientations,
            corner_permutation,
        ) = self._validate_corners(cube)

        errors.extend(corner_errors)

        # ====================================================================
        # Edge validation
        # ====================================================================

        (
            edge_errors,
            edge_orientations,
            edge_permutation,
        ) = self._validate_edges(cube)

        errors.extend(edge_errors)

        # ====================================================================
        # Orientation constraints
        # ====================================================================

        corner_orientation_sum = sum(
            corner_orientations
        )

        edge_orientation_sum = sum(
            edge_orientations
        )

        if corner_orientation_sum % 3 != 0:
            errors.append(
                "Corner orientation is impossible: "
                "corner orientation sum is not divisible by 3."
            )

        if edge_orientation_sum % 2 != 0:
            errors.append(
                "Edge orientation is impossible: "
                "edge orientation sum is not even."
            )

        # ====================================================================
        # Permutation parity
        # ====================================================================

        corner_parity = self._permutation_parity(
            corner_permutation
        )

        edge_parity = self._permutation_parity(
            edge_permutation
        )

        if (
            corner_parity != edge_parity
            and -1 not in corner_permutation
            and -1 not in edge_permutation
        ):
            errors.append(
                "Permutation parity is impossible: "
                "corner and edge permutations have different parity."
            )

        # ====================================================================
        # Final result
        # ====================================================================

        valid = len(errors) == 0

        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            sticker_count=sticker_count,
            color_counts=color_counts,
            corner_orientation_sum=corner_orientation_sum,
            edge_orientation_sum=edge_orientation_sum,
            corner_permutation_parity=corner_parity,
            edge_permutation_parity=edge_parity,
        )

    # ========================================================================
    # Structure
    # ========================================================================

    @staticmethod
    def _validate_structure(
        cube: CubeState,
    ) -> list[str]:
        """
        Validate the basic CubeState structure.
        """

        errors: list[str] = []

        if not hasattr(cube, "faces"):
            errors.append(
                "CubeState does not contain a faces attribute."
            )
            return errors

        faces = cube.faces

        if not isinstance(faces, dict):
            errors.append(
                "CubeState.faces must be a dictionary."
            )
            return errors

        actual_faces = set(faces.keys())
        expected_faces = set(FACE_NAMES)

        missing = expected_faces - actual_faces
        extra = actual_faces - expected_faces

        if missing:
            errors.append(
                "Missing cube faces: "
                + ", ".join(sorted(missing))
            )

        if extra:
            errors.append(
                "Unexpected cube faces: "
                + ", ".join(sorted(extra))
            )

        if len(actual_faces) != EXPECTED_FACE_COUNT:
            errors.append(
                f"Expected {EXPECTED_FACE_COUNT} faces, "
                f"found {len(actual_faces)}."
            )

        for face in FACE_NAMES:

            if face not in faces:
                continue

            grid = faces[face]

            if not isinstance(grid, list):
                errors.append(
                    f"Face {face} must be a 3x3 list."
                )
                continue

            if len(grid) != GRID_SIZE:
                errors.append(
                    f"Face {face} must contain "
                    f"{GRID_SIZE} rows."
                )
                continue

            for row_index, row in enumerate(grid):

                if not isinstance(row, list):
                    errors.append(
                        f"Face {face} row {row_index} "
                        "must be a list."
                    )
                    continue

                if len(row) != GRID_SIZE:
                    errors.append(
                        f"Face {face} row {row_index} "
                        f"must contain {GRID_SIZE} stickers."
                    )

        return errors

    # ========================================================================
    # Flatten
    # ========================================================================

    @staticmethod
    def _flatten_cube(
        cube: CubeState,
    ) -> list[str]:
        """
        Flatten all 54 stickers into a list.
        """

        stickers: list[str] = []

        for face in FACE_NAMES:

            grid = cube.faces[face]

            for row in grid:

                for color in row:
                    stickers.append(
                        str(color).lower()
                    )

        return stickers

    # ========================================================================
    # Color counting
    # ========================================================================

    @staticmethod
    def _count_colors(
        stickers: list[str],
    ) -> dict[str, int]:
        """
        Count occurrences of every color.
        """

        counts = {
            color: 0
            for color in sorted(VALID_COLORS)
        }

        for sticker in stickers:

            counts[sticker] = (
                counts.get(sticker, 0) + 1
            )

        return counts

    # ========================================================================
    # Color validation
    # ========================================================================

    @staticmethod
    def _validate_colors(
        stickers: list[str],
        color_counts: dict[str, int],
    ) -> list[str]:
        """
        Validate sticker colors and color counts.
        """

        errors: list[str] = []

        if len(stickers) != EXPECTED_STICKER_COUNT:
            errors.append(
                f"Expected {EXPECTED_STICKER_COUNT} stickers, "
                f"found {len(stickers)}."
            )

        invalid_colors = sorted(
            {
                color
                for color in stickers
                if color not in VALID_COLORS
            }
        )

        if invalid_colors:
            errors.append(
                "Invalid colors found: "
                + ", ".join(invalid_colors)
            )

        for color in sorted(VALID_COLORS):

            count = color_counts.get(color, 0)

            if count != EXPECTED_COLOR_COUNT:
                errors.append(
                    f"Color '{color}' appears "
                    f"{count} times; expected "
                    f"{EXPECTED_COLOR_COUNT}."
                )

        return errors

    # ========================================================================
    # Center validation
    # ========================================================================

    @staticmethod
    def _validate_centers(
        cube: CubeState,
    ) -> list[str]:
        """
        Validate the six center stickers.
        """

        errors: list[str] = []

        centers: dict[str, str] = {}

        for face in FACE_NAMES:

            color = str(
                cube.faces[face][1][1]
            ).lower()

            centers[face] = color

        center_colors = list(centers.values())

        if len(set(center_colors)) != EXPECTED_FACE_COUNT:
            errors.append(
                "Cube centers must contain "
                "six unique colors."
            )

        for face, expected_color in EXPECTED_CENTERS.items():

            actual_color = centers.get(face)

            if actual_color != expected_color:
                errors.append(
                    f"Center mismatch on face {face}: "
                    f"expected '{expected_color}', "
                    f"found '{actual_color}'."
                )

        return errors

    # ========================================================================
    # Corner validation
    # ========================================================================

    def _validate_corners(
        self,
        cube: CubeState,
    ) -> tuple[
        list[str],
        list[int],
        list[int],
    ]:
        """
        Validate all eight corner cubies.

        Returns:

            errors
            orientations
            permutation
        """

        errors: list[str] = []
        orientations: list[int] = []
        permutation: list[int] = []
        seen: set[int] = set()

        for index, facelets in enumerate(CORNER_FACELETS):

            colors = [
                self._get_sticker(
                    cube,
                    face,
                    row,
                    col,
                )
                for face, row, col in facelets
            ]

            color_set = frozenset(colors)

            if color_set not in CORNER_COLORS:

                errors.append(
                    "Invalid corner cubie at "
                    f"position {index}: "
                    f"{colors}"
                )

                orientations.append(0)
                permutation.append(-1)

                continue

            cubie_index = CORNER_COLORS.index(
                color_set
            )

            if cubie_index in seen:
                errors.append(
                    "Duplicate corner cubie detected: "
                    f"{sorted(color_set)}"
                )

            seen.add(cubie_index)

            permutation.append(cubie_index)

            orientation = self._corner_orientation(
                colors,
                facelets,
            )

            orientations.append(orientation)

        if len(seen) != len(CORNER_COLORS):
            errors.append(
                "Cube does not contain exactly "
                "one of each corner cubie."
            )

        return (
            errors,
            orientations,
            permutation,
        )

    # ========================================================================
    # Corner orientation
    # ========================================================================

    @staticmethod
    def _corner_orientation(
        colors: list[str],
        facelets: tuple[
            tuple[str, int, int],
            tuple[str, int, int],
            tuple[str, int, int],
        ],
    ) -> int:
        """
        Determine corner orientation.

        The orientation is determined by the location of the
        white/yellow sticker.

        The CORNER_FACELETS definitions intentionally use different
        handedness for the U-layer and D-layer corners.

        Therefore the orientation mapping is:

        U-layer:

            UD sticker on U -> 0
            UD sticker on F/B/L/R -> according to the local
            corner ordering.

        D-layer:

            The side-face orientation is reversed relative to
            the U-layer.

        This method does NOT assume that the three sticker colors
        must appear as a cyclic rotation of the canonical color
        tuple.

        That assumption is incorrect when a cubie moves between
        U-layer and D-layer positions.

        Returns:

            0 = correctly oriented
            1 = clockwise twist
            2 = counter-clockwise twist
        """

        # --------------------------------------------------------------------
        # Find the white/yellow sticker.
        #
        # Every valid corner contains exactly one U/D color.
        # --------------------------------------------------------------------

        ud_index = -1

        for index, color in enumerate(colors):

            if color in ("white", "yellow"):
                ud_index = index
                break

        # --------------------------------------------------------------------
        # A malformed corner will already be reported by the cubie
        # identity validation.
        #
        # Return 0 here so that orientation checking does not generate
        # misleading secondary errors.
        # --------------------------------------------------------------------

        if ud_index == -1:
            return 0

        # --------------------------------------------------------------------
        # U-layer corners.
        #
        # Example:
        #
        # UFR:
        #
        #     U -> 0
        #     F -> 1
        #     R -> 2
        #
        # URB:
        #
        #     U -> 0
        #     R -> 1
        #     B -> 2
        #
        # UBL:
        #
        #     U -> 0
        #     B -> 1
        #     L -> 2
        #
        # ULF:
        #
        #     U -> 0
        #     L -> 1
        #     F -> 2
        # --------------------------------------------------------------------

        if facelets[0][0] == "U":

            return ud_index

        # --------------------------------------------------------------------
        # D-layer corners.
        #
        # The D-layer facelet definitions have opposite handedness.
        #
        # Therefore the side-face orientations are reversed:
        #
        #     D -> 0
        #     second side -> 2
        #     third side  -> 1
        #
        # Example:
        #
        # DFR:
        #
        #     D -> 0
        #     F -> 2
        #     R -> 1
        #
        # DRB:
        #
        #     D -> 0
        #     R -> 2
        #     B -> 1
        #
        # DBL:
        #
        #     D -> 0
        #     B -> 2
        #     L -> 1
        #
        # DLF:
        #
        #     D -> 0
        #     L -> 2
        #     F -> 1
        # --------------------------------------------------------------------

        return (-ud_index) % 3

    
    # ========================================================================
    # Edge validation
    # ========================================================================

    def _validate_edges(
        self,
        cube: CubeState,
    ) -> tuple[
        list[str],
        list[int],
        list[int],
    ]:
        """
        Validate all twelve edge cubies.
        """

        errors: list[str] = []
        orientations: list[int] = []
        permutation: list[int] = []
        seen: set[int] = set()

        for index, facelets in enumerate(EDGE_FACELETS):

            colors = [
                self._get_sticker(
                    cube,
                    face,
                    row,
                    col,
                )
                for face, row, col in facelets
            ]

            color_set = frozenset(colors)

            if color_set not in EDGE_COLORS:

                errors.append(
                    "Invalid edge cubie at "
                    f"position {index}: "
                    f"{colors}"
                )

                orientations.append(0)
                permutation.append(-1)

                continue

            cubie_index = EDGE_COLORS.index(
                color_set
            )

            if cubie_index in seen:
                errors.append(
                    "Duplicate edge cubie detected: "
                    f"{sorted(color_set)}"
                )

            seen.add(cubie_index)

            permutation.append(cubie_index)

            orientation = self._edge_orientation(
                colors,
                facelets,
            )

            orientations.append(orientation)

        if len(seen) != len(EDGE_COLORS):
            errors.append(
                "Cube does not contain exactly "
                "one of each edge cubie."
            )

        return (
            errors,
            orientations,
            permutation,
        )

    # ========================================================================
    # Edge orientation
    # ========================================================================

    @staticmethod
    def _edge_orientation(
        colors: list[str],
        facelets: tuple[
            tuple[str, int, int],
            tuple[str, int, int],
        ],
    ) -> int:
        """
        Determine edge orientation.

        Standard orientation rules:

        If an edge contains white/yellow:

            0 = white/yellow is on U/D
            1 = white/yellow is on F/B/R/L

        If an edge does not contain white/yellow but
        contains green/blue:

            0 = green/blue is on F/B
            1 = green/blue is on R/L

        Otherwise:

            1 = flipped
        """

        faces = (
            facelets[0][0],
            facelets[1][0],
        )

        # ====================================================================
        # Edges containing white/yellow
        # ====================================================================

        if "white" in colors or "yellow" in colors:

            target = (
                "white"
                if "white" in colors
                else "yellow"
            )

            for color, face in zip(colors, faces):

                if (
                    color == target
                    and face in ("U", "D")
                ):
                    return 0

            return 1

        # ====================================================================
        # Middle-layer edges
        # ====================================================================

        if "green" in colors or "blue" in colors:

            target = (
                "green"
                if "green" in colors
                else "blue"
            )

            for color, face in zip(colors, faces):

                if (
                    color == target
                    and face in ("F", "B")
                ):
                    return 0

            return 1

        return 1

    # ========================================================================
    # Sticker access
    # ========================================================================

    @staticmethod
    def _get_sticker(
        cube: CubeState,
        face: str,
        row: int,
        col: int,
    ) -> str:
        """
        Safely retrieve one sticker.
        """

        return str(
            cube.faces[face][row][col]
        ).lower()

    # ========================================================================
    # Permutation parity
    # ========================================================================

    @staticmethod
    def _permutation_parity(
        permutation: list[int],
    ) -> int:
        """
        Return permutation parity.

        Returns:

            0 = even
            1 = odd
        """

        if any(value < 0 for value in permutation):
            return 0

        inversions = 0

        for i in range(len(permutation)):

            for j in range(i + 1, len(permutation)):

                if permutation[i] > permutation[j]:
                    inversions += 1

        return inversions % 2


# ============================================================================
# Convenience functions
# ============================================================================

def validate_cube(
    cube: CubeState,
) -> ValidationResult:
    """
    Validate a CubeState.
    """

    validator = CubeValidator()

    return validator.validate(cube)


def is_valid_cube(
    cube: CubeState,
) -> bool:
    """
    Return True if the cube is physically valid.
    """

    return validate_cube(cube).valid


# ============================================================================
# Demo helpers
# ============================================================================

def _create_solved_cube() -> CubeState:
    """
    Create a standard solved cube.

    This must match the color scheme used by move.py.
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

    return CubeState(faces)


# ============================================================================
# Demo
# ============================================================================

def main() -> None:

    print("CubeAI Cube Validator")
    print("---------------------")
    print()

    # ========================================================================
    # Solved cube
    # ========================================================================

    cube = _create_solved_cube()

    result = validate_cube(cube)

    print("Solved cube:")

    print(
        f"  Valid: {result.valid}"
    )

    print(
        f"  Stickers: {result.sticker_count}"
    )

    print(
        f"  Color counts: {result.color_counts}"
    )

    print(
        f"  Corner orientation sum: "
        f"{result.corner_orientation_sum}"
    )

    print(
        f"  Edge orientation sum: "
        f"{result.edge_orientation_sum}"
    )

    print(
        f"  Corner parity: "
        f"{result.corner_permutation_parity}"
    )

    print(
        f"  Edge parity: "
        f"{result.edge_permutation_parity}"
    )

    if result.errors:

        print()
        print("Errors:")

        for error in result.errors:
            print(f"  - {error}")

    print()

    # ========================================================================
    # Move engine integration
    # ========================================================================

    try:

        from move import apply_algorithm

        algorithm = "R U R' U' F2 L D"

        scrambled = apply_algorithm(
            cube,
            algorithm,
        )

        scrambled_result = validate_cube(
            scrambled
        )

        print("Scrambled cube:")

        print(
            f"  Algorithm: {algorithm}"
        )

        print(
            f"  Valid: {scrambled_result.valid}"
        )

        print(
            f"  Color counts: "
            f"{scrambled_result.color_counts}"
        )

        print(
            f"  Corner orientation sum: "
            f"{scrambled_result.corner_orientation_sum}"
        )

        print(
            f"  Edge orientation sum: "
            f"{scrambled_result.edge_orientation_sum}"
        )

        print(
            f"  Corner parity: "
            f"{scrambled_result.corner_permutation_parity}"
        )

        print(
            f"  Edge parity: "
            f"{scrambled_result.edge_permutation_parity}"
        )

        if scrambled_result.errors:

            print()
            print("Errors:")

            for error in scrambled_result.errors:
                print(f"  - {error}")

    except Exception as exc:

        print(
            "Move engine integration skipped:"
        )

        print(
            f"  {exc}"
        )

    print()

    # ========================================================================
    # Invalid color test
    # ========================================================================

    invalid_cube = _create_solved_cube()

    invalid_cube.faces["U"][0][0] = "purple"

    invalid_result = validate_cube(
        invalid_cube
    )

    print("Invalid color test:")

    print(
        f"  Rejected: "
        f"{not invalid_result.valid}"
    )

    print()

    # ========================================================================
    # Invalid color-count test
    # ========================================================================

    invalid_cube = _create_solved_cube()

    invalid_cube.faces["U"][0][0] = "yellow"

    invalid_result = validate_cube(
        invalid_cube
    )

    print("Invalid color-count test:")

    print(
        f"  Rejected: "
        f"{not invalid_result.valid}"
    )

    print()

    # ========================================================================
    # Solved cube must always pass
    # ========================================================================

    solved_test = validate_cube(
        _create_solved_cube()
    )

    print("Solved cube validation:")

    print(
        f"  PASS: {solved_test.valid}"
    )

    print()

    print("Cube validator ready!")


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()
