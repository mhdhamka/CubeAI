"""
CubeAI - Cubie Representation

Represents a Rubik's Cube using its physical pieces (cubies)
instead of individual face stickers.

A standard 3x3 Rubik's Cube contains:

    8 corner cubies
    12 edge cubies
    6 fixed center pieces

This module does NOT:

    - scan images
    - classify colors
    - solve the cube
    - perform moves

Its responsibility is to provide the low-level cubie
representation required by the cube engine and solver.

Pipeline:

    Vision CubeState
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
"""


from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ============================================================================
# Constants
# ============================================================================

CORNER_COUNT = 8
EDGE_COUNT = 12

CORNER_ORIENTATIONS = 3
EDGE_ORIENTATIONS = 2


# ============================================================================
# Corner names
# ============================================================================

"""
Corner positions.

Naming convention:

    UFR = Up-Front-Right
    URB = Up-Right-Back
    UBL = Up-Back-Left
    ULF = Up-Left-Front
    DFR = Down-Front-Right
    DRB = Down-Right-Back
    DBL = Down-Back-Left
    DLF = Down-Left-Front
"""

UFR = 0
URB = 1
UBL = 2
ULF = 3
DFR = 4
DRB = 5
DBL = 6
DLF = 7


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


# ============================================================================
# Edge names
# ============================================================================

"""
Edge positions.

Naming convention:

    UF = Up-Front
    UR = Up-Right
    UB = Up-Back
    UL = Up-Left

    FR = Front-Right
    RB = Right-Back
    BL = Back-Left
    LF = Left-Front

    DF = Down-Front
    DR = Down-Right
    DB = Down-Back
    DL = Down-Left
"""

UF = 0
UR = 1
UB = 2
UL = 3
FR = 4
RB = 5
BL = 6
LF = 7
DF = 8
DR = 9
DB = 10
DL = 11


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
# Color constants
# ============================================================================

WHITE = "white"
YELLOW = "yellow"
RED = "red"
ORANGE = "orange"
GREEN = "green"
BLUE = "blue"


VALID_COLORS = {
    WHITE,
    YELLOW,
    RED,
    ORANGE,
    GREEN,
    BLUE,
}


# ============================================================================
# Standard cubie color definitions
# ============================================================================

"""
Each cubie has a fixed combination of colors.

The order is important because orientation calculations depend
on the sticker order.

Corners:

    UFR = U R F
    URB = U R B
    UBL = U B L
    ULF = U L F

    DFR = D F R
    DRB = D R B
    DBL = D B L
    DLF = D L F


Edges:

    UF = U F
    UR = U R
    UB = U B
    UL = U L

    FR = F R
    RB = R B
    BL = B L
    LF = L F

    DF = D F
    DR = D R
    DB = D B
    DL = D L
"""

CORNER_COLORS = (
    (WHITE, RED, GREEN),       # UFR
    (WHITE, RED, BLUE),        # URB
    (WHITE, BLUE, ORANGE),     # UBL
    (WHITE, ORANGE, GREEN),    # ULF

    (YELLOW, GREEN, RED),      # DFR
    (YELLOW, RED, BLUE),       # DRB
    (YELLOW, BLUE, ORANGE),    # DBL
    (YELLOW, ORANGE, GREEN),   # DLF
)


EDGE_COLORS = (
    (WHITE, GREEN),            # UF
    (WHITE, RED),              # UR
    (WHITE, BLUE),              # UB
    (WHITE, ORANGE),            # UL

    (GREEN, RED),              # FR
    (RED, BLUE),               # RB
    (BLUE, ORANGE),             # BL
    (ORANGE, GREEN),            # LF

    (YELLOW, GREEN),           # DF
    (YELLOW, RED),              # DR
    (YELLOW, BLUE),             # DB
    (YELLOW, ORANGE),           # DL
)


# ============================================================================
# Helper functions
# ============================================================================

def _validate_corner_index(index: int) -> None:
    """Validate a corner position index."""

    if not isinstance(index, int):
        raise TypeError(
            "Corner index must be an integer."
        )

    if not 0 <= index < CORNER_COUNT:
        raise ValueError(
            f"Invalid corner index: {index}."
        )


def _validate_edge_index(index: int) -> None:
    """Validate an edge position index."""

    if not isinstance(index, int):
        raise TypeError(
            "Edge index must be an integer."
        )

    if not 0 <= index < EDGE_COUNT:
        raise ValueError(
            f"Invalid edge index: {index}."
        )


def _validate_corner_orientation(
    orientation: int,
) -> None:
    """Validate a corner orientation."""

    if not isinstance(orientation, int):
        raise TypeError(
            "Corner orientation must be an integer."
        )

    if not 0 <= orientation < CORNER_ORIENTATIONS:
        raise ValueError(
            "Corner orientation must be 0, 1, or 2."
        )


def _validate_edge_orientation(
    orientation: int,
) -> None:
    """Validate an edge orientation."""

    if not isinstance(orientation, int):
        raise TypeError(
            "Edge orientation must be an integer."
        )

    if not 0 <= orientation < EDGE_ORIENTATIONS:
        raise ValueError(
            "Edge orientation must be 0 or 1."
        )


# ============================================================================
# Corner cubie
# ============================================================================

@dataclass
class CornerCubie:
    """
    Represents one corner cubie.

    Attributes
    ----------
    piece:
        Which physical corner piece this is.

    orientation:
        Corner orientation:

            0 = correctly oriented
            1 = twisted clockwise
            2 = twisted counter-clockwise
    """

    piece: int
    orientation: int = 0

    def __post_init__(self) -> None:

        _validate_corner_index(
            self.piece
        )

        _validate_corner_orientation(
            self.orientation
        )

    @property
    def name(self) -> str:
        """Return the corner piece name."""

        return CORNER_NAMES[self.piece]

    @property
    def colors(self) -> tuple[str, str, str]:
        """Return the solved colors of this corner."""

        return CORNER_COLORS[self.piece]

    def copy(self) -> "CornerCubie":
        """Return a copy of the cubie."""

        return CornerCubie(
            piece=self.piece,
            orientation=self.orientation,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible representation."""

        return {
            "piece": self.piece,
            "name": self.name,
            "colors": list(self.colors),
            "orientation": self.orientation,
        }


# ============================================================================
# Edge cubie
# ============================================================================

@dataclass
class EdgeCubie:
    """
    Represents one edge cubie.

    Attributes
    ----------
    piece:
        Which physical edge piece this is.

    orientation:
        Edge orientation:

            0 = correctly oriented
            1 = flipped
    """

    piece: int
    orientation: int = 0

    def __post_init__(self) -> None:

        _validate_edge_index(
            self.piece
        )

        _validate_edge_orientation(
            self.orientation
        )

    @property
    def name(self) -> str:
        """Return the edge piece name."""

        return EDGE_NAMES[self.piece]

    @property
    def colors(self) -> tuple[str, str]:
        """Return the solved colors of this edge."""

        return EDGE_COLORS[self.piece]

    def copy(self) -> "EdgeCubie":
        """Return a copy of the cubie."""

        return EdgeCubie(
            piece=self.piece,
            orientation=self.orientation,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible representation."""

        return {
            "piece": self.piece,
            "name": self.name,
            "colors": list(self.colors),
            "orientation": self.orientation,
        }


# ============================================================================
# Cubie State
# ============================================================================

class CubieState:
    """
    Complete Rubik's Cube cubie representation.

    The cube is represented using:

        corners[8]
        edges[12]

    Each corner stores:

        piece identity
        orientation

    Each edge stores:

        piece identity
        orientation

    A solved cube therefore looks like:

        Corners:
            UFR -> UFR
            URB -> URB
            UBL -> UBL
            ULF -> ULF
            DFR -> DFR
            DRB -> DRB
            DBL -> DBL
            DLF -> DLF

        Edges:
            UF -> UF
            UR -> UR
            UB -> UB
            UL -> UL
            FR -> FR
            RB -> RB
            BL -> BL
            LF -> LF
            DF -> DF
            DR -> DR
            DB -> DB
            DL -> DL

    This class does NOT perform moves.
    """

    def __init__(
        self,
        corners: list[CornerCubie] | None = None,
        edges: list[EdgeCubie] | None = None,
    ) -> None:

        if corners is None:

            self.corners = [
                CornerCubie(
                    piece=index
                )
                for index in range(
                    CORNER_COUNT
                )
            ]

        else:

            self.corners = [
                corner.copy()
                for corner in corners
            ]

        if edges is None:

            self.edges = [
                EdgeCubie(
                    piece=index
                )
                for index in range(
                    EDGE_COUNT
                )
            ]

        else:

            self.edges = [
                edge.copy()
                for edge in edges
            ]

        self._validate_structure()

    # ========================================================================
    # Structure validation
    # ========================================================================

    def _validate_structure(self) -> None:
        """Validate the cubie arrays."""

        if len(self.corners) != CORNER_COUNT:

            raise ValueError(
                "CubieState must contain exactly "
                "8 corners."
            )

        if len(self.edges) != EDGE_COUNT:

            raise ValueError(
                "CubieState must contain exactly "
                "12 edges."
            )

        corner_pieces = [
            corner.piece
            for corner in self.corners
        ]

        if len(set(corner_pieces)) != CORNER_COUNT:

            raise ValueError(
                "Each corner piece must appear "
                "exactly once."
            )

        edge_pieces = [
            edge.piece
            for edge in self.edges
        ]

        if len(set(edge_pieces)) != EDGE_COUNT:

            raise ValueError(
                "Each edge piece must appear "
                "exactly once."
            )

    # ========================================================================
    # Solved state
    # ========================================================================

    def is_solved(self) -> bool:
        """
        Return True when the cube is solved.
        """

        for position, corner in enumerate(
            self.corners
        ):

            if corner.piece != position:
                return False

            if corner.orientation != 0:
                return False

        for position, edge in enumerate(
            self.edges
        ):

            if edge.piece != position:
                return False

            if edge.orientation != 0:
                return False

        return True

    # ========================================================================
    # Copy
    # ========================================================================

    def copy(self) -> "CubieState":
        """Return an independent copy."""

        return CubieState(
            corners=self.corners,
            edges=self.edges,
        )

    # ========================================================================
    # Corner access
    # ========================================================================

    def get_corner(
        self,
        position: int,
    ) -> CornerCubie:
        """Return a copy of a corner at a position."""

        _validate_corner_index(
            position
        )

        return self.corners[position].copy()

    def set_corner(
        self,
        position: int,
        piece: int,
        orientation: int = 0,
    ) -> None:
        """Set a corner at a position."""

        _validate_corner_index(
            position
        )

        self.corners[position] = CornerCubie(
            piece=piece,
            orientation=orientation,
        )

        self._validate_structure()

    # ========================================================================
    # Edge access
    # ========================================================================

    def get_edge(
        self,
        position: int,
    ) -> EdgeCubie:
        """Return a copy of an edge at a position."""

        _validate_edge_index(
            position
        )

        return self.edges[position].copy()

    def set_edge(
        self,
        position: int,
        piece: int,
        orientation: int = 0,
    ) -> None:
        """Set an edge at a position."""

        _validate_edge_index(
            position
        )

        self.edges[position] = EdgeCubie(
            piece=piece,
            orientation=orientation,
        )

        self._validate_structure()

    # ========================================================================
    # Orientation sums
    # ========================================================================

    def corner_orientation_sum(self) -> int:
        """
        Return the total corner orientation.

        A physically valid cube must have:

            sum % 3 == 0
        """

        return sum(
            corner.orientation
            for corner in self.corners
        )

    def edge_orientation_sum(self) -> int:
        """
        Return the total edge orientation.

        A physically valid cube must have:

            sum % 2 == 0
        """

        return sum(
            edge.orientation
            for edge in self.edges
        )

    # ========================================================================
    # Permutation parity
    # ========================================================================

    @staticmethod
    def _permutation_parity(
        permutation: list[int],
    ) -> int:
        """
        Calculate permutation parity.

        Returns:

            0 = even
            1 = odd
        """

        inversions = 0

        for i in range(
            len(permutation)
        ):

            for j in range(
                i + 1,
                len(permutation),
            ):

                if permutation[i] > permutation[j]:

                    inversions += 1

        return inversions % 2

    def corner_parity(self) -> int:
        """Return corner permutation parity."""

        return self._permutation_parity(
            [
                corner.piece
                for corner in self.corners
            ]
        )

    def edge_parity(self) -> int:
        """Return edge permutation parity."""

        return self._permutation_parity(
            [
                edge.piece
                for edge in self.edges
            ]
        )

    # ========================================================================
    # Validation
    # ========================================================================

    def validate(self) -> dict[str, Any]:
        """
        Validate the physical cubie representation.

        Checks:

            - correct number of pieces
            - unique corner pieces
            - unique edge pieces
            - corner orientation sum
            - edge orientation sum
            - permutation parity
        """

        errors: list[str] = []

        # --------------------------------------------------------------------
        # Structure
        # --------------------------------------------------------------------

        try:

            self._validate_structure()

        except Exception as exc:

            errors.append(
                str(exc)
            )

        # --------------------------------------------------------------------
        # Corner orientation
        # --------------------------------------------------------------------

        if (
            self.corner_orientation_sum() % 3
            != 0
        ):

            errors.append(
                "Corner orientation sum is invalid."
            )

        # --------------------------------------------------------------------
        # Edge orientation
        # --------------------------------------------------------------------

        if (
            self.edge_orientation_sum() % 2
            != 0
        ):

            errors.append(
                "Edge orientation sum is invalid."
            )

        # --------------------------------------------------------------------
        # Permutation parity
        # --------------------------------------------------------------------

        if (
            self.corner_parity()
            != self.edge_parity()
        ):

            errors.append(
                "Corner and edge permutation "
                "parities do not match."
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    # ========================================================================
    # Dictionary
    # ========================================================================

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible cubie state."""

        return {
            "corners": [
                corner.to_dict()
                for corner in self.corners
            ],
            "edges": [
                edge.to_dict()
                for edge in self.edges
            ],
        }

    # ========================================================================
    # String representation
    # ========================================================================

    def __str__(self) -> str:
        """Return human-readable cubie state."""

        lines: list[str] = []

        lines.append(
            "Corners:"
        )

        for position, corner in enumerate(
            self.corners
        ):

            lines.append(
                f"  {CORNER_NAMES[position]}: "
                f"{corner.name} "
                f"(orientation={corner.orientation})"
            )

        lines.append("")

        lines.append(
            "Edges:"
        )

        for position, edge in enumerate(
            self.edges
        ):

            lines.append(
                f"  {EDGE_NAMES[position]}: "
                f"{edge.name} "
                f"(orientation={edge.orientation})"
            )

        return "\n".join(lines)


# ============================================================================
# Factory
# ============================================================================

def create_solved_cubie_state() -> CubieState:
    """
    Create a solved CubieState.
    """

    return CubieState()


# ============================================================================
# Demo
# ============================================================================

def main() -> None:

    print(
        "CubeAI Cubie State"
    )

    print(
        "------------------"
    )

    print()

    cube = CubieState()

    print(
        "Solved cubie state:"
    )

    print()

    print(cube)

    print()

    print(
        f"Solved: {cube.is_solved()}"
    )

    print(
        f"Corner orientation sum: "
        f"{cube.corner_orientation_sum()}"
    )

    print(
        f"Edge orientation sum: "
        f"{cube.edge_orientation_sum()}"
    )

    print(
        f"Corner parity: "
        f"{cube.corner_parity()}"
    )

    print(
        f"Edge parity: "
        f"{cube.edge_parity()}"
    )

    print()

    validation = cube.validate()

    print(
        "Validation:"
    )

    print(
        f"  Valid: "
        f"{validation['valid']}"
    )

    if validation["errors"]:

        for error in validation["errors"]:

            print(
                f"  - {error}"
            )

    print()

    print(
        "JSON:"
    )

    import json

    print(
        json.dumps(
            cube.to_dict(),
            indent=2,
        )
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()