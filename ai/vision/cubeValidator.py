"""
CubeAI - Cube Validator

Validates a completed Rubik's Cube scan.

Responsibilities:

    ScanSession
         |
         v
    CubeValidator
         |
         +--> Check all six faces exist
         +--> Check each face is 3x3
         +--> Check exactly 54 stickers
         +--> Check exactly 9 stickers of each color
         +--> Check center colors
         +--> Check face/color mapping
         |
         v
    Valid / Invalid cube scan

This module does NOT solve the cube.

It only determines whether the scanned color data
is structurally valid enough to continue to the
cube-state / solver pipeline.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
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
# Constants
# ============================================================================

EXPECTED_FACES = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)

GRID_SIZE = 3

STICKERS_PER_FACE = 9

TOTAL_STICKERS = 54

EXPECTED_COLOR_COUNT = 9


# Standard CubeAI color scheme
COLOR_TO_FACE = {
    "white": "U",
    "red": "R",
    "green": "F",
    "yellow": "D",
    "orange": "L",
    "blue": "B",
}

FACE_TO_COLOR = {
    face: color
    for color, face in COLOR_TO_FACE.items()
}


VALID_COLORS = set(
    COLOR_TO_FACE.keys()
)


# ============================================================================
# Validation Result
# ============================================================================

@dataclass
class ValidationResult:
    """
    Result of validating a complete cube scan.
    """

    valid: bool

    faces: list[str]

    color_counts: dict[str, int]

    center_colors: dict[str, Optional[str]]

    warnings: list[str]

    errors: list[str]

    confidence: float

    def to_dict(self) -> dict[str, Any]:
        """
        Convert validation result to JSON-compatible dictionary.
        """

        return {
            "valid": self.valid,
            "faces": self.faces,
            "color_counts": self.color_counts,
            "center_colors": self.center_colors,
            "warnings": self.warnings,
            "errors": self.errors,
            "confidence": self.confidence,
        }


# ============================================================================
# Cube Validator
# ============================================================================

class CubeValidator:
    """
    Validates the complete Rubik's Cube scan.

    Input:

        ScanSession

    Output:

        ValidationResult
    """

    def __init__(
        self,
        expected_faces: tuple[str, ...] = EXPECTED_FACES,
    ) -> None:

        self.expected_faces = tuple(
            expected_faces
        )

    # ========================================================================
    # Public API
    # ========================================================================

    def validate(
        self,
        session: Any,
    ) -> ValidationResult:

        errors: list[str] = []

        warnings: list[str] = []

        # --------------------------------------------------------------------
        # Extract faces from session
        # --------------------------------------------------------------------

        faces = self._extract_faces(
            session
        )

        # --------------------------------------------------------------------
        # Check all six faces
        # --------------------------------------------------------------------

        missing_faces = [
            face
            for face in self.expected_faces
            if face not in faces
        ]

        if missing_faces:

            errors.append(
                "Missing faces: "
                + ", ".join(
                    missing_faces
                )
            )

        # --------------------------------------------------------------------
        # Check duplicate / unexpected faces
        # --------------------------------------------------------------------

        unexpected_faces = [
            face
            for face in faces
            if face not in self.expected_faces
        ]

        if unexpected_faces:

            errors.append(
                "Unexpected faces: "
                + ", ".join(
                    unexpected_faces
                )
            )

        # --------------------------------------------------------------------
        # Validate individual face grids
        # --------------------------------------------------------------------

        all_stickers: list[str] = []

        for face in self.expected_faces:

            if face not in faces:
                continue

            grid = faces[face]

            if not self._is_valid_grid(
                grid
            ):

                errors.append(
                    f"Face {face} does not contain "
                    "a valid 3x3 color grid."
                )

                continue

            for row in grid:

                for color in row:

                    all_stickers.append(
                        self._normalize_color(
                            color
                        )
                    )

        # --------------------------------------------------------------------
        # Total sticker count
        # --------------------------------------------------------------------

        if len(all_stickers) != TOTAL_STICKERS:

            errors.append(
                f"Expected {TOTAL_STICKERS} stickers, "
                f"found {len(all_stickers)}."
            )

        # --------------------------------------------------------------------
        # Check colors
        # --------------------------------------------------------------------

        color_counts = {
            color: 0
            for color in sorted(
                VALID_COLORS
            )
        }

        invalid_colors: list[str] = []

        for color in all_stickers:

            if color not in VALID_COLORS:

                invalid_colors.append(
                    color
                )

            else:

                color_counts[color] += 1

        if invalid_colors:

            errors.append(
                "Invalid colors detected: "
                + ", ".join(
                    sorted(
                        set(
                            invalid_colors
                        )
                    )
                )
            )

        # --------------------------------------------------------------------
        # Every color must appear exactly 9 times
        # --------------------------------------------------------------------

        for color in sorted(
            VALID_COLORS
        ):

            count = color_counts[color]

            if count != EXPECTED_COLOR_COUNT:

                errors.append(
                    f"Color '{color}' appears "
                    f"{count} times; expected "
                    f"{EXPECTED_COLOR_COUNT}."
                )

        # --------------------------------------------------------------------
        # Validate center colors
        # --------------------------------------------------------------------

        center_colors = (
            self._get_center_colors(
                faces
            )
        )

        for face in self.expected_faces:

            expected_color = FACE_TO_COLOR[
                face
            ]

            actual_color = center_colors.get(
                face
            )

            if actual_color is None:

                continue

            if actual_color != expected_color:

                errors.append(
                    f"Face {face} has center "
                    f"color '{actual_color}', "
                    f"expected '{expected_color}'."
                )

        # --------------------------------------------------------------------
        # Check that each center color is unique
        # --------------------------------------------------------------------

        known_centers = [
            color
            for color in center_colors.values()
            if color is not None
        ]

        if len(
            set(known_centers)
        ) != len(known_centers):

            errors.append(
                "Duplicate center colors detected."
            )

        # --------------------------------------------------------------------
        # Confidence
        # --------------------------------------------------------------------

        confidence = self._calculate_confidence(
            session,
            errors,
        )

        # --------------------------------------------------------------------
        # Final result
        # --------------------------------------------------------------------

        valid = (
            len(errors) == 0
            and len(all_stickers) == TOTAL_STICKERS
        )

        return ValidationResult(
            valid=valid,
            faces=[
                face
                for face in self.expected_faces
                if face in faces
            ],
            color_counts=color_counts,
            center_colors=center_colors,
            warnings=warnings,
            errors=errors,
            confidence=confidence,
        )

    # ========================================================================
    # Extract faces
    # ========================================================================

    @staticmethod
    def _extract_faces(
        session: Any,
    ) -> dict[str, Any]:

        # --------------------------------------------------------------------
        # Session object
        # --------------------------------------------------------------------

        if hasattr(
            session,
            "faces",
        ):

            faces = session.faces

            if isinstance(
                faces,
                dict,
            ):

                return dict(faces)

        # --------------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------------

        if isinstance(
            session,
            dict,
        ):

            faces = session.get(
                "faces",
                {}
            )

            if isinstance(
                faces,
                dict,
            ):

                return dict(faces)

        return {}

    # ========================================================================
    # Grid validation
    # ========================================================================

    @staticmethod
    def _is_valid_grid(
        grid: Any,
    ) -> bool:

        if not isinstance(
            grid,
            (list, tuple),
        ):

            return False

        if len(grid) != GRID_SIZE:

            return False

        for row in grid:

            if not isinstance(
                row,
                (list, tuple),
            ):

                return False

            if len(row) != GRID_SIZE:

                return False

        return True

    # ========================================================================
    # Center colors
    # ========================================================================

    @staticmethod
    def _get_center_colors(
        faces: dict[str, Any],
    ) -> dict[str, Optional[str]]:

        result: dict[
            str,
            Optional[str]
        ] = {}

        for face in EXPECTED_FACES:

            grid = faces.get(
                face
            )

            if not CubeValidator._is_valid_grid(
                grid
            ):

                result[face] = None

                continue

            center = grid[1][1]

            result[face] = (
                CubeValidator._normalize_color(
                    center
                )
            )

        return result

    # ========================================================================
    # Color normalization
    # ========================================================================

    @staticmethod
    def _normalize_color(
        color: Any,
    ) -> str:

        if color is None:

            return "unknown"

        normalized = str(
            color
        ).strip().lower()

        aliases = {
            "w": "white",
            "y": "yellow",
            "r": "red",
            "o": "orange",
            "g": "green",
            "b": "blue",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    # ========================================================================
    # Confidence
    # ========================================================================

    @staticmethod
    def _calculate_confidence(
        session: Any,
        errors: list[str],
    ) -> float:

        # --------------------------------------------------------------------
        # Start with session confidence when available.
        # --------------------------------------------------------------------

        session_confidence = 1.0

        if hasattr(
            session,
            "confidence",
        ):

            try:

                session_confidence = float(
                    session.confidence
                )

            except (
                TypeError,
                ValueError,
            ):

                session_confidence = 1.0

        elif isinstance(
            session,
            dict,
        ):

            try:

                session_confidence = float(
                    session.get(
                        "confidence",
                        1.0,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                session_confidence = 1.0

        session_confidence = max(
            0.0,
            min(
                1.0,
                session_confidence,
            ),
        )

        # --------------------------------------------------------------------
        # Invalid cube should never receive full confidence.
        # --------------------------------------------------------------------

        if errors:

            return round(
                session_confidence * 0.5,
                4,
            )

        return round(
            session_confidence,
            4,
        )


# ============================================================================
# Convenience function
# ============================================================================

def validate_session(
    session: Any,
) -> ValidationResult:

    validator = CubeValidator()

    return validator.validate(
        session
    )


# ============================================================================
# CLI test
# ============================================================================

def main() -> None:

    print(
        "CubeAI Cube Validator"
    )

    print(
        "---------------------"
    )

    print()

    # ------------------------------------------------------------------------
    # Create a complete test cube.
    #
    # Each face is solved according to the CubeAI color scheme.
    # ------------------------------------------------------------------------

    test_faces = {

        "U": [
            ["white", "white", "white"],
            ["white", "white", "white"],
            ["white", "white", "white"],
        ],

        "R": [
            ["red", "red", "red"],
            ["red", "red", "red"],
            ["red", "red", "red"],
        ],

        "F": [
            ["green", "green", "green"],
            ["green", "green", "green"],
            ["green", "green", "green"],
        ],

        "D": [
            ["yellow", "yellow", "yellow"],
            ["yellow", "yellow", "yellow"],
            ["yellow", "yellow", "yellow"],
        ],

        "L": [
            ["orange", "orange", "orange"],
            ["orange", "orange", "orange"],
            ["orange", "orange", "orange"],
        ],

        "B": [
            ["blue", "blue", "blue"],
            ["blue", "blue", "blue"],
            ["blue", "blue", "blue"],
        ],
    }

    # ------------------------------------------------------------------------
    # Minimal mock session.
    # ------------------------------------------------------------------------

    class TestSession:

        def __init__(self) -> None:

            self.faces = test_faces

            self.confidence = 1.0

    session = TestSession()

    print(
        "Validating test cube..."
    )

    print()

    result = validate_session(
        session
    )

    # ------------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------------

    if result.valid:

        print(
            "Cube validation successful!"
        )

    else:

        print(
            "Cube validation failed!"
        )

    print()

    print(
        f"Valid:      {result.valid}"
    )

    print(
        f"Confidence: {result.confidence:.2f}"
    )

    print()

    print(
        "Faces:"
    )

    for face in result.faces:

        print(
            f"  {face}: "
            f"{result.center_colors.get(face)}"
        )

    print()

    print(
        "Color counts:"
    )

    for color, count in sorted(
        result.color_counts.items()
    ):

        print(
            f"  {color:<7} {count}"
        )

    if result.warnings:

        print()

        print(
            "Warnings:"
        )

        for warning in result.warnings:

            print(
                f"  - {warning}"
            )

    if result.errors:

        print()

        print(
            "Errors:"
        )

        for error in result.errors:

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