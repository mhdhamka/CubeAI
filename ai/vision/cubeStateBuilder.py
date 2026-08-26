"""
CubeAI - Cube State Builder

Converts the completed vision scan session into the engine's
CubeState representation.

Pipeline:

    ScanSession
         |
         v
    CubeStateBuilder
         |
         v
    engine.CubeState
         |
         v
    CubeState.validate()
         |
         v
    Solver / Move Engine

This module does NOT:

    - detect the cube
    - detect stickers
    - classify colors
    - solve the cube
    - modify CubeState after construction

Its responsibility is to convert the completed vision/session
representation into a validated engine CubeState.
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

ENGINE_DIR = os.path.abspath(
    os.path.join(
        CURRENT_DIR,
        "..",
        "engine",
    )
)

if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)


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

GRID_SIZE = 3
EXPECTED_FACES = 6
EXPECTED_STICKERS = 54


# ============================================================================
# Build Result
# ============================================================================

class CubeStateBuildResult:
    """
    Result produced by CubeStateBuilder.

    Attributes
    ----------
    success:
        True when a CubeState was successfully constructed
        and validated.

    cube:
        The resulting CubeState.

    confidence:
        Scan-session confidence.

    scanned_faces:
        Faces supplied by the scan session.

    missing_faces:
        Faces that were not supplied.

    errors:
        Fatal errors.

    warnings:
        Non-fatal warnings.
    """

    def __init__(
        self,
        success: bool,
        cube: Optional[Any] = None,
        confidence: float = 0.0,
        scanned_faces: Optional[list[str]] = None,
        missing_faces: Optional[list[str]] = None,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
    ) -> None:

        self.success = bool(success)

        self.cube = cube

        self.confidence = float(
            confidence
        )

        self.scanned_faces = (
            list(scanned_faces)
            if scanned_faces is not None
            else []
        )

        self.missing_faces = (
            list(missing_faces)
            if missing_faces is not None
            else []
        )

        self.errors = (
            list(errors)
            if errors is not None
            else []
        )

        self.warnings = (
            list(warnings)
            if warnings is not None
            else []
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result into JSON-compatible data.
        """

        cube_dict = None

        if self.cube is not None:

            if hasattr(
                self.cube,
                "to_dict",
            ):

                cube_dict = (
                    self.cube.to_dict()
                )

        return {
            "success": self.success,
            "confidence": self.confidence,
            "scanned_faces": self.scanned_faces,
            "missing_faces": self.missing_faces,
            "errors": self.errors,
            "warnings": self.warnings,
            "cube": cube_dict,
        }


# ============================================================================
# Cube State Builder
# ============================================================================

class CubeStateBuilder:
    """
    Converts a completed ScanSession into CubeState.
    """

    def __init__(
        self,
        require_complete: bool = True,
        validate: bool = True,
    ) -> None:

        self.require_complete = bool(
            require_complete
        )

        self.validate_state = bool(
            validate
        )

    # ========================================================================
    # Public API
    # ========================================================================

    def build(
        self,
        session: Any,
    ) -> CubeStateBuildResult:
        """
        Build a CubeState from a ScanSession.

        Expected session representation:

            session.faces = {
                "U": [[...], [...], [...]],
                "R": [[...], [...], [...]],
                "F": [[...], [...], [...]],
                "D": [[...], [...], [...]],
                "L": [[...], [...], [...]],
                "B": [[...], [...], [...]]
            }

        The session may also expose:

            session.confidence
            session.complete
            session.scanned_faces
            session.missing_faces
        """

        # --------------------------------------------------------------------
        # Check CubeState import
        # --------------------------------------------------------------------

        if CubeState is None:

            return self._failure(
                "CubeState could not be imported: "
                f"{CUBE_STATE_IMPORT_ERROR}"
            )

        # --------------------------------------------------------------------
        # Check session
        # --------------------------------------------------------------------

        if session is None:

            return self._failure(
                "Scan session cannot be None."
            )

        # --------------------------------------------------------------------
        # Extract faces
        # --------------------------------------------------------------------

        faces = self._get_faces(
            session
        )

        if faces is None:

            return self._failure(
                "Scan session does not contain "
                "a faces collection."
            )

        if not isinstance(
            faces,
            dict,
        ):

            return self._failure(
                "Scan session faces must be a dictionary."
            )

        # --------------------------------------------------------------------
        # Determine scanned and missing faces
        # --------------------------------------------------------------------

        scanned_faces = [
            face
            for face in FACE_NAMES
            if face in faces
        ]

        missing_faces = [
            face
            for face in FACE_NAMES
            if face not in faces
        ]

        confidence = self._get_confidence(
            session
        )

        print(
            "CubeAI Cube State Builder"
        )

        print(
            "-------------------------"
        )

        print()

        print(
            "Building CubeState..."
        )

        print(
            f"  Scanned faces: "
            f"{len(scanned_faces)}/{EXPECTED_FACES}"
        )

        print(
            f"  Confidence: "
            f"{confidence:.2f}"
        )

        if scanned_faces:

            print(
                f"  Faces: "
                f"{' '.join(scanned_faces)}"
            )

        if missing_faces:

            print(
                f"  Missing: "
                f"{' '.join(missing_faces)}"
            )

        # --------------------------------------------------------------------
        # Require complete scan
        # --------------------------------------------------------------------

        session_complete = self._get_complete(
            session
        )

        if self.require_complete:

            if len(missing_faces) > 0:

                return CubeStateBuildResult(
                    success=False,
                    confidence=confidence,
                    scanned_faces=scanned_faces,
                    missing_faces=missing_faces,
                    errors=[
                        "Cannot build CubeState because "
                        "the scan session is incomplete.",
                        "Missing faces: "
                        + ", ".join(missing_faces),
                    ],
                )

            if session_complete is False:

                return CubeStateBuildResult(
                    success=False,
                    confidence=confidence,
                    scanned_faces=scanned_faces,
                    missing_faces=missing_faces,
                    errors=[
                        "Scan session reports that "
                        "the cube scan is incomplete."
                    ],
                )

        # --------------------------------------------------------------------
        # Validate and normalize faces
        # --------------------------------------------------------------------

        normalized_faces: dict[
            str,
            list[list[str]]
        ] = {}

        errors: list[str] = []
        warnings: list[str] = []

        for face in FACE_NAMES:

            if face not in faces:
                continue

            try:

                normalized_faces[face] = (
                    self._normalize_face(
                        faces[face],
                        face,
                    )
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                errors.append(
                    f"{face} face is invalid: "
                    f"{exc}"
                )

        if errors:

            return CubeStateBuildResult(
                success=False,
                confidence=confidence,
                scanned_faces=scanned_faces,
                missing_faces=missing_faces,
                errors=errors,
                warnings=warnings,
            )

        # --------------------------------------------------------------------
        # Build engine CubeState
        # --------------------------------------------------------------------

        try:

            cube = CubeState(
                faces=normalized_faces
            )

        except Exception as exc:

            return CubeStateBuildResult(
                success=False,
                confidence=confidence,
                scanned_faces=scanned_faces,
                missing_faces=missing_faces,
                errors=[
                    "Failed to construct CubeState: "
                    f"{exc}"
                ],
                warnings=warnings,
            )

        print()
        print(
            "CubeState created successfully."
        )

        # --------------------------------------------------------------------
        # Validate CubeState
        # --------------------------------------------------------------------

        if self.validate_state:

            validation = cube.validate()

            if not validation.valid:

                errors.extend(
                    validation.errors
                )

            warnings.extend(
                validation.warnings
            )

            print()
            print(
                "CubeState validation:"
            )

            print(
                f"  Valid: "
                f"{validation.valid}"
            )

            if validation.errors:

                print(
                    "  Errors:"
                )

                for error in validation.errors:

                    print(
                        f"    - {error}"
                    )

            if validation.warnings:

                print(
                    "  Warnings:"
                )

                for warning in validation.warnings:

                    print(
                        f"    - {warning}"
                    )

        # --------------------------------------------------------------------
        # Final result
        # --------------------------------------------------------------------

        if errors:

            return CubeStateBuildResult(
                success=False,
                cube=cube,
                confidence=confidence,
                scanned_faces=scanned_faces,
                missing_faces=missing_faces,
                errors=errors,
                warnings=warnings,
            )

        print()
        print(
            "CubeState build successful!"
        )

        return CubeStateBuildResult(
            success=True,
            cube=cube,
            confidence=confidence,
            scanned_faces=scanned_faces,
            missing_faces=missing_faces,
            errors=[],
            warnings=warnings,
        )

    # ========================================================================
    # Face extraction
    # ========================================================================

    @staticmethod
    def _get_faces(
        session: Any,
    ) -> Optional[dict[str, Any]]:
        """
        Extract the faces dictionary.

        Supports both:

            session.faces

        and:

            {
                "faces": {...}
            }
        """

        if isinstance(
            session,
            dict,
        ):

            return session.get(
                "faces"
            )

        if hasattr(
            session,
            "faces",
        ):

            return getattr(
                session,
                "faces",
            )

        # CubeScanSession keeps FaceScan objects private and exposes its
        # normalized face matrices through build_result().
        if hasattr(session, "build_result"):
            result = session.build_result()
            if hasattr(result, "faces"):
                return getattr(result, "faces")

        return None

    # ========================================================================
    # Complete state
    # ========================================================================

    @staticmethod
    def _get_complete(
        session: Any,
    ) -> Optional[bool]:
        """
        Get the session completion state.

        Returns None when the session does not expose
        a completion flag.
        """

        if isinstance(
            session,
            dict,
        ):

            value = session.get(
                "complete"
            )

        elif hasattr(
            session,
            "complete",
        ):

            value = getattr(
                session,
                "complete",
            )

        else:
            if hasattr(session, "is_complete"):
                return bool(session.is_complete())
            return None

        if value is None:
            return None

        return bool(value)

    # ========================================================================
    # Face normalization
    # ========================================================================

    @staticmethod
    def _normalize_face(
        colors: Any,
        face: str,
    ) -> list[list[str]]:
        """
        Validate and normalize a 3x3 face.
        """

        if face not in FACE_NAMES:

            raise ValueError(
                f"Invalid face '{face}'."
            )

        if not isinstance(
            colors,
            (list, tuple),
        ):

            raise TypeError(
                "Face must be a 3x3 list."
            )

        if len(colors) != GRID_SIZE:

            raise ValueError(
                "Face must contain exactly 3 rows."
            )

        normalized: list[list[str]] = []

        for row_index, row in enumerate(
            colors
        ):

            if not isinstance(
                row,
                (list, tuple),
            ):

                raise TypeError(
                    f"Row {row_index} must be a list."
                )

            if len(row) != GRID_SIZE:

                raise ValueError(
                    f"Row {row_index} must contain "
                    "exactly 3 colors."
                )

            normalized_row: list[str] = []

            for col_index, color in enumerate(
                row
            ):

                normalized_color = (
                    CubeStateBuilder._normalize_color(
                        color
                    )
                )

                if normalized_color not in VALID_COLORS:

                    raise ValueError(
                        f"Invalid color at "
                        f"{face}[{row_index}]"
                        f"[{col_index}]: "
                        f"{color!r}"
                    )

                normalized_row.append(
                    normalized_color
                )

            normalized.append(
                normalized_row
            )

        return normalized

    # ========================================================================
    # Color normalization
    # ========================================================================

    @staticmethod
    def _normalize_color(
        color: Any,
    ) -> str:
        """
        Normalize scanner color names.

        Supported aliases:

            W -> white
            Y -> yellow
            R -> red
            O -> orange
            G -> green
            B -> blue
        """

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
    def _get_confidence(
        session: Any,
    ) -> float:
        """
        Get aggregate scan confidence.
        """

        if isinstance(
            session,
            dict,
        ):

            value = session.get(
                "confidence",
                0.0,
            )

        elif hasattr(
            session,
            "confidence",
        ):

            value = getattr(
                session,
                "confidence",
                0.0,
            )

        else:

            value = 0.0

        try:

            value = float(value)

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

        return max(
            0.0,
            min(
                1.0,
                value,
            )
        )

    # ========================================================================
    # Failure
    # ========================================================================

    @staticmethod
    def _failure(
        error: str,
    ) -> CubeStateBuildResult:

        return CubeStateBuildResult(
            success=False,
            cube=None,
            confidence=0.0,
            scanned_faces=[],
            missing_faces=list(
                FACE_NAMES
            ),
            errors=[
                error
            ],
            warnings=[],
        )


# ============================================================================
# Convenience function
# ============================================================================

def build_cube_state(
    session: Any,
) -> CubeStateBuildResult:
    """
    Build a validated CubeState from a completed ScanSession.
    """

    builder = CubeStateBuilder()

    return builder.build(
        session
    )


# ============================================================================
# Demo / CLI
# ============================================================================

def main() -> None:

    print(
        "CubeAI Cube State Builder"
    )

    print(
        "-------------------------"
    )

    print()

    # ------------------------------------------------------------------------
    # Solved cube test
    #
    # This verifies that the conversion layer correctly creates
    # an engine CubeState and that CubeState.validate() accepts
    # a structurally valid cube.
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
    # Session-like object
    # ------------------------------------------------------------------------

    class TestSession:

        def __init__(self) -> None:

            self.faces = test_faces

            self.confidence = 1.0

            self.complete = True

    session = TestSession()

    # ------------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------------

    result = build_cube_state(
        session
    )

    print()

    if not result.success:

        print(
            "CubeState build failed!"
        )

        print()

        for error in result.errors:

            print(
                f"  - {error}"
            )

        return

    print(
        "CubeState:"
    )

    print()

    for face in FACE_NAMES:

        print(
            f"  {face}:"
        )

        for row in result.cube.faces[face]:

            print(
                "    "
                + " ".join(row)
            )

    print()

    print(
        "Complete:",
        result.cube.is_complete()
    )

    print(
        "Unknown stickers:",
        result.cube.unknown_count()
    )

    print()

    print(
        "Color counts:"
    )

    counts = (
        result.cube.color_counts()
    )

    for color in sorted(counts):

        print(
            f"  {color:<7}: "
            f"{counts[color]}"
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