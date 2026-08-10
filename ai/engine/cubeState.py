"""
CubeAI - Cube State

Represents and validates the complete state of a Rubik's Cube.

Pipeline:

    CubeScanner
         |
         v
    3x3 face colors
         |
         v
    CubeState
         |
         v
    Cube validation
         |
         v
    Solver / Move Engine

The CubeState class does NOT solve the cube.

Its responsibility is to provide a reliable, structured,
validated representation of the cube that later engine
components can work with.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


# ============================================================================
# Constants
# ============================================================================

GRID_SIZE = 3
STICKERS_PER_FACE = 9
FACE_COUNT = 6
TOTAL_STICKERS = 54

VALID_COLORS = {
    "white",
    "yellow",
    "red",
    "orange",
    "green",
    "blue",
}

EXPECTED_COLOR_COUNT = 9

UNKNOWN_COLOR = "unknown"


# ============================================================================
# Face names
# ============================================================================

UP = "U"
RIGHT = "R"
FRONT = "F"
DOWN = "D"
LEFT = "L"
BACK = "B"

FACE_NAMES = (
    UP,
    RIGHT,
    FRONT,
    DOWN,
    LEFT,
    BACK,
)


# ============================================================================
# Color → face mapping
# ============================================================================

COLOR_TO_FACE = {
    "white": UP,
    "red": RIGHT,
    "green": FRONT,
    "yellow": DOWN,
    "orange": LEFT,
    "blue": BACK,
}


FACE_TO_COLOR = {
    face: color
    for color, face in COLOR_TO_FACE.items()
}


# ============================================================================
# Data structures
# ============================================================================

@dataclass(frozen=True)
class FaceState:
    """
    Represents one Rubik's Cube face.

    The grid is stored row-major:

        0 1 2
        3 4 5
        6 7 8
    """

    name: str
    colors: tuple[tuple[str, str, str],
                  tuple[str, str, str],
                  tuple[str, str, str]]

    @property
    def center(self) -> str:
        """
        Return the center sticker color.
        """

        return self.colors[1][1]

    def flatten(self) -> list[str]:
        """
        Return the face as nine colors.
        """

        return [
            color
            for row in self.colors
            for color in row
        ]

    def to_list(self) -> list[list[str]]:
        """
        Return a mutable-style 3x3 list representation.
        """

        return [
            list(row)
            for row in self.colors
        ]


@dataclass
class CubeValidation:
    """
    Result of cube-state validation.
    """

    valid: bool
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# ============================================================================
# Cube State
# ============================================================================

class CubeState:
    """
    Complete Rubik's Cube state.

    A cube contains six faces:

        U
        R
        F
        D
        L
        B

    Each face contains exactly nine stickers.

    The state is represented using color names rather than
    cubie coordinates because this is the format produced
    by the vision pipeline.
    """

    def __init__(
        self,
        faces: Optional[
            dict[str, list[list[str]]]
        ] = None,
    ) -> None:

        self.faces: dict[str, list[list[str]]] = {}

        for face in FACE_NAMES:
            self.faces[face] = self._empty_face()

        if faces is not None:
            for face, colors in faces.items():
                self.set_face(face, colors)

    # ========================================================================
    # Face helpers
    # ========================================================================

    @staticmethod
    def _empty_face() -> list[list[str]]:
        return [
            [UNKNOWN_COLOR, UNKNOWN_COLOR, UNKNOWN_COLOR],
            [UNKNOWN_COLOR, UNKNOWN_COLOR, UNKNOWN_COLOR],
            [UNKNOWN_COLOR, UNKNOWN_COLOR, UNKNOWN_COLOR],
        ]

    @staticmethod
    def _validate_face_name(
        face: str,
    ) -> None:

        if face not in FACE_NAMES:
            raise ValueError(
                f"Invalid face '{face}'. "
                f"Expected one of {FACE_NAMES}."
            )

    @staticmethod
    def _validate_grid(
        colors: list[list[str]],
    ) -> None:

        if not isinstance(colors, list):
            raise TypeError(
                "Face colors must be a 3x3 list."
            )

        if len(colors) != GRID_SIZE:
            raise ValueError(
                "Face must contain exactly 3 rows."
            )

        for row in colors:

            if not isinstance(row, list):
                raise TypeError(
                    "Each face row must be a list."
                )

            if len(row) != GRID_SIZE:
                raise ValueError(
                    "Each face row must contain "
                    "exactly 3 colors."
                )

            for color in row:

                if not isinstance(color, str):
                    raise TypeError(
                        "Sticker colors must be strings."
                    )

    # ========================================================================
    # Set face
    # ========================================================================

    def set_face(
        self,
        face: str,
        colors: list[list[str]],
    ) -> None:
        """
        Store a scanned 3x3 face.

        Example:

            cube.set_face(
                "F",
                [
                    ["green", "green", "green"],
                    ["green", "green", "green"],
                    ["green", "green", "green"],
                ],
            )
        """

        self._validate_face_name(face)
        self._validate_grid(colors)

        self.faces[face] = [
            list(row)
            for row in colors
        ]

    # ========================================================================
    # Get face
    # ========================================================================

    def get_face(
        self,
        face: str,
    ) -> list[list[str]]:

        self._validate_face_name(face)

        return [
            list(row)
            for row in self.faces[face]
        ]

    # ========================================================================
    # Set scanned face
    # ========================================================================

    def set_scanned_face(
        self,
        colors: list[list[str]],
        face: Optional[str] = None,
    ) -> str:
        """
        Add a scanned face to the cube.

        If face is not supplied, the center sticker determines
        the face automatically.

        For a standard color scheme:

            white  -> U
            red    -> R
            green  -> F
            yellow -> D
            orange -> L
            blue   -> B

        Returns the resolved face name.
        """

        self._validate_grid(colors)

        center = colors[1][1].lower()

        if face is None:

            if center not in COLOR_TO_FACE:
                raise ValueError(
                    f"Cannot determine cube face from "
                    f"center color '{center}'."
                )

            face = COLOR_TO_FACE[center]

        self.set_face(
            face,
            colors,
        )

        return face

    # ========================================================================
    # Center colors
    # ========================================================================

    def centers(self) -> dict[str, str]:
        """
        Return all currently known center colors.
        """

        return {
            face: self.faces[face][1][1]
            for face in FACE_NAMES
        }

    # ========================================================================
    # Completion
    # ========================================================================

    def is_complete(self) -> bool:
        """
        Return True when all 54 stickers have known colors.
        """

        for face in FACE_NAMES:

            for row in self.faces[face]:

                for color in row:

                    if color == UNKNOWN_COLOR:
                        return False

        return True

    # ========================================================================
    # Unknown stickers
    # ========================================================================

    def unknown_count(self) -> int:
        """
        Return number of unknown stickers.
        """

        count = 0

        for face in FACE_NAMES:

            for row in self.faces[face]:

                for color in row:

                    if color == UNKNOWN_COLOR:
                        count += 1

        return count

    # ========================================================================
    # Color counts
    # ========================================================================

    def color_counts(self) -> dict[str, int]:
        """
        Count every color currently present.
        """

        counts = {
            color: 0
            for color in VALID_COLORS
        }

        for face in FACE_NAMES:

            for row in self.faces[face]:

                for color in row:

                    if color in counts:
                        counts[color] += 1

        return counts

    # ========================================================================
    # Validation
    # ========================================================================

    def validate(self) -> CubeValidation:
        """
        Validate the currently stored cube state.

        This performs structural/color-count validation.

        It intentionally does not yet perform full cubie
        permutation/orientation legality checks. Those belong
        to the deeper cube engine.
        """

        errors: list[str] = []
        warnings: list[str] = []

        # --------------------------------------------------------------------
        # Check unknown stickers
        # --------------------------------------------------------------------

        unknown = self.unknown_count()

        if unknown > 0:

            errors.append(
                f"Cube has {unknown} unknown sticker(s)."
            )

        # --------------------------------------------------------------------
        # Check colors
        # --------------------------------------------------------------------

        invalid_colors: set[str] = set()

        for face in FACE_NAMES:

            for row in self.faces[face]:

                for color in row:

                    if (
                        color != UNKNOWN_COLOR
                        and color not in VALID_COLORS
                    ):
                        invalid_colors.add(color)

        if invalid_colors:

            errors.append(
                "Invalid colors found: "
                + ", ".join(
                    sorted(invalid_colors)
                )
            )

        # --------------------------------------------------------------------
        # Color counts
        # --------------------------------------------------------------------

        counts = self.color_counts()

        for color in VALID_COLORS:

            count = counts[color]

            if count != EXPECTED_COLOR_COUNT:

                errors.append(
                    f"Color '{color}' appears "
                    f"{count} times; expected "
                    f"{EXPECTED_COLOR_COUNT}."
                )

        # --------------------------------------------------------------------
        # Center colors
        # --------------------------------------------------------------------

        center_colors = list(
            self.centers().values()
        )

        known_centers = [
            color
            for color in center_colors
            if color != UNKNOWN_COLOR
        ]

        if len(set(known_centers)) != len(known_centers):

            errors.append(
                "Duplicate center colors detected."
            )

        # --------------------------------------------------------------------
        # Basic face-center consistency
        # --------------------------------------------------------------------

        for face in FACE_NAMES:

            center = self.faces[face][1][1]

            if center != UNKNOWN_COLOR:

                expected_color = FACE_TO_COLOR[face]

                if center != expected_color:

                    errors.append(
                        f"Face '{face}' has center "
                        f"'{center}', expected "
                        f"'{expected_color}'."
                    )

        # --------------------------------------------------------------------
        # Validation status
        # --------------------------------------------------------------------

        return CubeValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    # ========================================================================
    # Flatten
    # ========================================================================

    def flatten(
        self,
        order: tuple[str, ...] = FACE_NAMES,
    ) -> list[str]:
        """
        Flatten the cube into one 54-sticker list.

        Default order:

            U R F D L B
        """

        result: list[str] = []

        for face in order:

            self._validate_face_name(face)

            result.extend(
                color
                for row in self.faces[face]
                for color in row
            )

        return result

    # ========================================================================
    # Dictionary
    # ========================================================================

    def to_dict(self) -> dict[str, list[list[str]]]:
        """
        Return the complete cube state.
        """

        return {
            face: self.get_face(face)
            for face in FACE_NAMES
        }

    # ========================================================================
    # String representation
    # ========================================================================

    def __str__(self) -> str:
        """
        Human-readable cube state.
        """

        lines: list[str] = []

        for face in FACE_NAMES:

            lines.append(
                f"{face}:"
            )

            for row in self.faces[face]:

                lines.append(
                    "  " + " ".join(row)
                )

        return "\n".join(lines)

    # ========================================================================
    # Factory from scanner results
    # ========================================================================

    @classmethod
    def from_scan_results(
        cls,
        scan_results: list[Any],
    ) -> "CubeState":
        """
        Build a CubeState from multiple CubeScanner results.

        Each result must contain:

            result.success
            result.colors

        The face is automatically identified using
        the center sticker.
        """

        cube = cls()

        for result in scan_results:

            if not getattr(
                result,
                "success",
                False,
            ):

                raise ValueError(
                    "Cannot build cube state from "
                    "an unsuccessful scan."
                )

            colors = getattr(
                result,
                "colors",
                None,
            )

            if colors is None:

                raise ValueError(
                    "Scan result does not contain colors."
                )

            cube.set_scanned_face(
                colors
            )

        return cube


# ============================================================================
# Convenience functions
# ============================================================================

def create_cube_state() -> CubeState:
    """
    Create an empty cube state.
    """

    return CubeState()


def cube_from_faces(
    faces: dict[str, list[list[str]]],
) -> CubeState:
    """
    Create a CubeState from six face grids.
    """

    return CubeState(
        faces=faces
    )


# ============================================================================
# Demo
# ============================================================================

def main() -> None:

    print("CubeAI Cube State")
    print("-----------------")

    cube = CubeState()

    # ------------------------------------------------------------------------
    # Demonstrate one scanned face.
    #
    # The center is green, therefore this becomes the F face.
    # ------------------------------------------------------------------------

    front = [
        ["green", "green", "red"],
        ["green", "green", "orange"],
        ["blue", "green", "yellow"],
    ]

    face = cube.set_scanned_face(
        front
    )

    print(
        f"Scanned face: {face}"
    )

    print()

    print(
        "Current cube:"
    )

    print(cube)

    print()

    print(
        f"Complete: "
        f"{cube.is_complete()}"
    )

    print(
        f"Unknown stickers: "
        f"{cube.unknown_count()}"
    )

    print()

    validation = cube.validate()

    print(
        f"Valid: "
        f"{validation.valid}"
    )

    if validation.errors:

        print(
            "Errors:"
        )

        for error in validation.errors:

            print(
                f"  - {error}"
            )

    print()

    print(
        "Color counts:"
    )

    for color, count in cube.color_counts().items():

        print(
            f"  {color:<7}: {count}"
        )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()