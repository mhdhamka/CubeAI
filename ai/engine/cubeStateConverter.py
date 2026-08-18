"""
CubeAI - Cube State Converter

Converts a color-based CubeState into the physical cubie
representation used by CubieState.

Pipeline:

    CubeState
         |
         v
    CubeStateConverter
         |
         v
    CubieState
         |
         v
    Move Engine
         |
         v
    Solver

This module does NOT:

    - scan images
    - detect stickers
    - classify colors
    - perform moves
    - solve the cube

Its responsibility is converting the 54-sticker color
representation into:

    8 corner pieces + orientations
    12 edge pieces + orientations
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional


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

    from cubeState import (
        CubeState,
        FACE_NAMES,
        COLOR_TO_FACE,
    )

except ImportError as exc:

    CubeState = None
    COLOR_TO_FACE = {}
    CUBE_STATE_IMPORT_ERROR = str(exc)

else:

    CUBE_STATE_IMPORT_ERROR = None


try:

    from cubie import (
        CubieState,
        CornerCubie,
        EdgeCubie,
        CORNER_COLORS,
        EDGE_COLORS,
        CORNER_NAMES,
        EDGE_NAMES,
    )

except ImportError as exc:

    CubieState = None
    CornerCubie = None
    EdgeCubie = None
    CORNER_COLORS = ()
    EDGE_COLORS = ()
    CORNER_NAMES = ()
    EDGE_NAMES = ()
    CUBIE_IMPORT_ERROR = str(exc)

else:

    CUBIE_IMPORT_ERROR = None


# ============================================================================
# Constants
# ============================================================================

FACE_ORDER = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)

GRID_SIZE = 3

VALID_COLORS = {
    "white",
    "yellow",
    "red",
    "orange",
    "green",
    "blue",
}


# ============================================================================
# Result
# ============================================================================

class CubeStateConversionResult:
    """
    Result of CubeState -> CubieState conversion.
    """

    def __init__(
        self,
        success: bool,
        cubie_state: Optional[Any] = None,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
    ) -> None:

        self.success = bool(success)

        self.cubie_state = cubie_state

        self.errors = (
            errors
            if errors is not None
            else []
        )

        self.warnings = (
            warnings
            if warnings is not None
            else []
        )

    def to_dict(self) -> dict[str, Any]:

        return {
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "cubie_state": (
                self.cubie_state.to_dict()
                if self.cubie_state is not None
                else None
            ),
        }


# ============================================================================
# Face sticker helpers
# ============================================================================

def _get_sticker(
    cube: CubeState,
    face: str,
    row: int,
    col: int,
) -> str:
    """
    Return one sticker color.
    """

    return cube.faces[face][row][col]


# ============================================================================
# Corner sticker mapping
# ============================================================================

"""
Each corner position is represented by three stickers.

The order follows the definitions in cubie.py:

    UFR = U R F
    URB = U R B
    UBL = U B L
    ULF = U L F

    DFR = D F R
    DRB = D R B
    DBL = D B L
    DLF = D L F
"""


CORNER_STICKERS = {

    # U layer

    "UFR": (
        ("U", 2, 2),
        ("R", 0, 0),
        ("F", 0, 2),
    ),

    "URB": (
        ("U", 0, 2),
        ("R", 0, 2),
        ("B", 0, 0),
    ),

    "UBL": (
        ("U", 0, 0),
        ("B", 0, 2),
        ("L", 0, 0),
    ),

    "ULF": (
        ("U", 2, 0),
        ("L", 0, 2),
        ("F", 0, 0),
    ),

    # D layer

    "DFR": (
        ("D", 0, 2),
        ("F", 2, 2),
        ("R", 2, 0),
    ),

    "DRB": (
        ("D", 2, 2),
        ("R", 2, 2),
        ("B", 2, 0),
    ),

    "DBL": (
        ("D", 2, 0),
        ("B", 2, 2),
        ("L", 2, 0),
    ),

    "DLF": (
        ("D", 0, 0),
        ("L", 2, 2),
        ("F", 2, 0),
    ),
}


# ============================================================================
# Edge sticker mapping
# ============================================================================

"""
Each edge position is represented by two stickers.

The order follows cubie.py:

    UF
    UR
    UB
    UL

    FR
    RB
    BL
    LF

    DF
    DR
    DB
    DL
"""


EDGE_STICKERS = {

    # U layer

    "UF": (
        ("U", 2, 1),
        ("F", 0, 1),
    ),

    "UR": (
        ("U", 1, 2),
        ("R", 0, 1),
    ),

    "UB": (
        ("U", 0, 1),
        ("B", 0, 1),
    ),

    "UL": (
        ("U", 1, 0),
        ("L", 0, 1),
    ),

    # Middle layer

    "FR": (
        ("F", 1, 2),
        ("R", 1, 0),
    ),

    "RB": (
        ("R", 1, 2),
        ("B", 1, 0),
    ),

    "BL": (
        ("B", 1, 2),
        ("L", 1, 0),
    ),

    "LF": (
        ("L", 1, 2),
        ("F", 1, 0),
    ),

    # D layer

    "DF": (
        ("D", 0, 1),
        ("F", 2, 1),
    ),

    "DR": (
        ("D", 1, 2),
        ("R", 2, 1),
    ),

    "DB": (
        ("D", 2, 1),
        ("B", 2, 1),
    ),

    "DL": (
        ("D", 1, 0),
        ("L", 2, 1),
    ),
}


# ============================================================================
# Converter
# ============================================================================

class CubeStateConverter:
    """
    Converts CubeState into CubieState.
    """

    def convert(
        self,
        cube: CubeState,
    ) -> CubeStateConversionResult:
        """
        Convert a complete CubeState into CubieState.
        """

        errors: list[str] = []
        warnings: list[str] = []

        # --------------------------------------------------------------------
        # Dependencies
        # --------------------------------------------------------------------

        if CubeState is None:

            return self._failure(
                "CubeState could not be imported: "
                f"{CUBE_STATE_IMPORT_ERROR}"
            )

        if CubieState is None:

            return self._failure(
                "CubieState could not be imported: "
                f"{CUBIE_IMPORT_ERROR}"
            )

        # --------------------------------------------------------------------
        # Input validation
        # --------------------------------------------------------------------

        if cube is None:

            return self._failure(
                "CubeState cannot be None."
            )

        if not isinstance(
            cube,
            CubeState,
        ):

            return self._failure(
                "Input must be a CubeState instance."
            )

        # --------------------------------------------------------------------
        # Cube completeness
        # --------------------------------------------------------------------

        if not cube.is_complete():

            return self._failure(
                "Cannot convert incomplete CubeState. "
                f"Unknown stickers: {cube.unknown_count()}."
            )

        # --------------------------------------------------------------------
        # Cube validation
        # --------------------------------------------------------------------

        validation = cube.validate()

        if not validation.valid:

            return self._failure(
                "CubeState is invalid.",
                errors=list(validation.errors),
            )

        # --------------------------------------------------------------------
        # Convert corners
        # --------------------------------------------------------------------

        corners: list[CornerCubie] = []

        for position, name in enumerate(
            CORNER_NAMES
        ):

            try:

                colors = self._corner_colors(
                    cube,
                    name,
                )

                piece, orientation = (
                    self._identify_corner(
                        colors
                    )
                )

                corners.append(
                    CornerCubie(
                        piece=piece,
                        orientation=orientation,
                    )
                )

            except Exception as exc:

                errors.append(
                    f"Corner {name} conversion failed: "
                    f"{exc}"
                )

        # --------------------------------------------------------------------
        # Convert edges
        # --------------------------------------------------------------------

        edges: list[EdgeCubie] = []

        for position, name in enumerate(
            EDGE_NAMES
        ):

            try:

                colors = self._edge_colors(
                    cube,
                    name,
                )

                piece, orientation = (
                    self._identify_edge(
                        colors
                    )
                )

                edges.append(
                    EdgeCubie(
                        piece=piece,
                        orientation=orientation,
                    )
                )

            except Exception as exc:

                errors.append(
                    f"Edge {name} conversion failed: "
                    f"{exc}"
                )

        # --------------------------------------------------------------------
        # Stop if individual conversion failed
        # --------------------------------------------------------------------

        if errors:

            return CubeStateConversionResult(
                success=False,
                cubie_state=None,
                errors=errors,
                warnings=warnings,
            )

        # --------------------------------------------------------------------
        # Build CubieState
        # --------------------------------------------------------------------

        try:

            cubie = CubieState(
                corners=corners,
                edges=edges,
            )

        except Exception as exc:

            return self._failure(
                "Failed to construct CubieState.",
                errors=[str(exc)],
            )

        # --------------------------------------------------------------------
        # Physical cubie validation
        # --------------------------------------------------------------------

        cubie_validation = cubie.validate()

        if not cubie_validation["valid"]:

            return CubeStateConversionResult(
                success=False,
                cubie_state=cubie,
                errors=list(
                    cubie_validation["errors"]
                ),
                warnings=warnings,
            )

        # --------------------------------------------------------------------
        # Success
        # --------------------------------------------------------------------

        return CubeStateConversionResult(
            success=True,
            cubie_state=cubie,
            errors=[],
            warnings=warnings,
        )

    # ========================================================================
    # Corner colors
    # ========================================================================

    @staticmethod
    def _corner_colors(
        cube: CubeState,
        position: str,
    ) -> tuple[str, str, str]:
        """
        Read the three stickers belonging to a corner.
        """

        stickers = CORNER_STICKERS[position]

        return tuple(
            _get_sticker(
                cube,
                face,
                row,
                col,
            )
            for face, row, col in stickers
        )

    # ========================================================================
    # Edge colors
    # ========================================================================

    @staticmethod
    def _edge_colors(
        cube: CubeState,
        position: str,
    ) -> tuple[str, str]:
        """
        Read the two stickers belonging to an edge.
        """

        stickers = EDGE_STICKERS[position]

        return tuple(
            _get_sticker(
                cube,
                face,
                row,
                col,
            )
            for face, row, col in stickers
        )

    # ========================================================================
    # Corner identification
    # ========================================================================

    @staticmethod
    def _identify_corner(
        colors: tuple[str, str, str],
    ) -> tuple[int, int]:
        """
        Identify a physical corner piece and orientation.

        Returns:

            (piece_index, orientation)
        """

        color_set = set(colors)

        if len(color_set) != 3:

            raise ValueError(
                f"Corner contains duplicate colors: "
                f"{colors}"
            )

        # Find physical piece by color combination.

        piece = None

        for index, expected in enumerate(
            CORNER_COLORS
        ):

            if color_set == set(expected):

                piece = index
                break

        if piece is None:

            raise ValueError(
                f"Unknown corner color combination: "
                f"{colors}"
            )

        expected = CORNER_COLORS[piece]

        # ---------------------------------------------------------------
        # Orientation
        #
        # The cubie definitions use the first color as the U/D color.
        #
        # orientation 0:
        #
        #     U/D color appears in first position
        #
        # orientation 1:
        #
        #     U/D color appears in second position
        #
        # orientation 2:
        #
        #     U/D color appears in third position
        # ---------------------------------------------------------------

        ud_color = (
            expected[0]
        )

        if colors[0] == ud_color:

            orientation = 0

        elif colors[1] == ud_color:

            orientation = 1

        elif colors[2] == ud_color:

            orientation = 2

        else:

            raise ValueError(
                f"Could not determine orientation "
                f"for corner {colors}."
            )

        return piece, orientation

    # ========================================================================
    # Edge identification
    # ========================================================================

    @staticmethod
    def _identify_edge(
        colors: tuple[str, str],
    ) -> tuple[int, int]:
        """
        Identify a physical edge piece and orientation.

        Returns:

            (piece_index, orientation)
        """

        color_set = set(colors)

        if len(color_set) != 2:

            raise ValueError(
                f"Edge contains duplicate colors: "
                f"{colors}"
            )

        piece = None

        for index, expected in enumerate(
            EDGE_COLORS
        ):

            if color_set == set(expected):

                piece = index
                break

        if piece is None:

            raise ValueError(
                f"Unknown edge color combination: "
                f"{colors}"
            )

        expected = EDGE_COLORS[piece]

        # ---------------------------------------------------------------
        # Edge orientation
        #
        # Orientation 0 means the colors appear in the
        # same order as the solved cubie definition.
        #
        # Example:
        #
        #     UF = (white, green)
        #
        #     (white, green) -> 0
        #     (green, white) -> 1
        # ---------------------------------------------------------------

        if colors == expected:

            orientation = 0

        elif colors == (
            expected[1],
            expected[0],
        ):

            orientation = 1

        else:

            raise ValueError(
                f"Could not determine orientation "
                f"for edge {colors}."
            )

        return piece, orientation

    # ========================================================================
    # Failure
    # ========================================================================

    @staticmethod
    def _failure(
        message: str,
        errors: Optional[list[str]] = None,
    ) -> CubeStateConversionResult:
        """
        Create a failed conversion result.
        """

        final_errors = [
            message
        ]

        if errors:

            final_errors.extend(
                errors
            )

        return CubeStateConversionResult(
            success=False,
            cubie_state=None,
            errors=final_errors,
            warnings=[],
        )


# ============================================================================
# Convenience function
# ============================================================================

def convert_cube_state(
    cube: CubeState,
) -> CubeStateConversionResult:
    """
    Convert CubeState into CubieState.
    """

    converter = CubeStateConverter()

    return converter.convert(
        cube
    )


# ============================================================================
# Demo
# ============================================================================

def main() -> None:

    print(
        "CubeAI Cube State Converter"
    )

    print(
        "---------------------------"
    )

    print()

    # ------------------------------------------------------------------------
    # Create a solved CubeState.
    # ------------------------------------------------------------------------

    solved_faces = {

        "U": [
            [
                "white",
                "white",
                "white",
            ],
            [
                "white",
                "white",
                "white",
            ],
            [
                "white",
                "white",
                "white",
            ],
        ],

        "R": [
            [
                "red",
                "red",
                "red",
            ],
            [
                "red",
                "red",
                "red",
            ],
            [
                "red",
                "red",
                "red",
            ],
        ],

        "F": [
            [
                "green",
                "green",
                "green",
            ],
            [
                "green",
                "green",
                "green",
            ],
            [
                "green",
                "green",
                "green",
            ],
        ],

        "D": [
            [
                "yellow",
                "yellow",
                "yellow",
            ],
            [
                "yellow",
                "yellow",
                "yellow",
            ],
            [
                "yellow",
                "yellow",
                "yellow",
            ],
        ],

        "L": [
            [
                "orange",
                "orange",
                "orange",
            ],
            [
                "orange",
                "orange",
                "orange",
            ],
            [
                "orange",
                "orange",
                "orange",
            ],
        ],

        "B": [
            [
                "blue",
                "blue",
                "blue",
            ],
            [
                "blue",
                "blue",
                "blue",
            ],
            [
                "blue",
                "blue",
                "blue",
            ],
        ],
    }

    # ------------------------------------------------------------------------
    # Build CubeState.
    # ------------------------------------------------------------------------

    cube = CubeState(
        solved_faces
    )

    print(
        "CubeState created."
    )

    print(
        f"Complete: {cube.is_complete()}"
    )

    validation = cube.validate()

    print(
        f"Valid: {validation.valid}"
    )

    print()

    if not validation.valid:

        print(
            "CubeState validation failed:"
        )

        for error in validation.errors:

            print(
                f"  - {error}"
            )

        return

    # ------------------------------------------------------------------------
    # Convert.
    # ------------------------------------------------------------------------

    result = convert_cube_state(
        cube
    )

    if not result.success:

        print(
            "Conversion failed!"
        )

        for error in result.errors:

            print(
                f"  - {error}"
            )

        return

    # ------------------------------------------------------------------------
    # Display result.
    # ------------------------------------------------------------------------

    cubie = result.cubie_state

    print(
        "Conversion successful!"
    )

    print()

    print(
        f"CubieState solved: "
        f"{cubie.is_solved()}"
    )

    print(
        f"Corner orientation sum: "
        f"{cubie.corner_orientation_sum()}"
    )

    print(
        f"Edge orientation sum: "
        f"{cubie.edge_orientation_sum()}"
    )

    print(
        f"Corner parity: "
        f"{cubie.corner_parity()}"
    )

    print(
        f"Edge parity: "
        f"{cubie.edge_parity()}"
    )

    print()

    print(
        "CubieState:"
    )

    print(
        cubie
    )

    print()

    print(
        "Validation:"
    )

    cubie_validation = cubie.validate()

    print(
        f"  Valid: "
        f"{cubie_validation['valid']}"
    )

    if cubie_validation["errors"]:

        for error in cubie_validation["errors"]:

            print(
                f"  - {error}"
            )

    print()

    print(
        "JSON:"
    )

    print(
        json.dumps(
            result.to_dict(),
            indent=2,
        )
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":

    main()