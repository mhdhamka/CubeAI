"""
CubeAI - Cube Scan Session

Collects six scanned Rubik's Cube faces and builds a complete
cube color state.

The single-face scanner remains responsible for:

    image
      ↓
    CubeDetector
      ↓
    FaceDetector
      ↓
    ColorClassifier
      ↓
    ScanResult

This module is responsible for:

    ScanResult
      ↓
    identify U/R/F/D/L/B
      ↓
    collect all six faces
      ↓
    validate color counts
      ↓
    build complete cube color state

Face mapping:

    white  -> U
    red    -> R
    green  -> F
    yellow -> D
    orange -> L
    blue   -> B

The resulting face order is:

    U
    R
    F
    D
    L
    B

This module does NOT perform cubie validation itself.
The completed color state can later be passed into CubeValidator.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
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
    from scanner import (
        CubeScanner,
        ScanResult,
        VALID_COLORS,
        COLOR_TO_FACE,
        FACE_TO_COLOR,
        EXPECTED_STICKERS,
        GRID_SIZE,
    )
except ImportError as exc:
    raise ImportError(
        "Could not import scanner.py. "
        f"Details: {exc}"
    ) from exc


# ============================================================================
# Constants
# ============================================================================

EXPECTED_FACES = 6

FACE_NAMES = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)

COLORS = (
    "white",
    "red",
    "green",
    "yellow",
    "orange",
    "blue",
)


# ============================================================================
# Data structures
# ============================================================================

@dataclass
class FaceScan:
    """
    Stores one successfully scanned cube face.
    """

    face_name: str
    face_color: str
    colors: list[list[str]]
    confidence: float

    warnings: list[str] = field(
        default_factory=list
    )


@dataclass
class CubeScanResult:
    """
    Complete six-face scanning result.
    """

    success: bool

    faces: dict[str, list[list[str]]]

    face_colors: dict[str, str]

    confidence: float

    scanned_faces: list[str]

    missing_faces: list[str]

    duplicate_faces: list[str]

    color_counts: dict[str, int]

    warnings: list[str] = field(
        default_factory=list
    )

    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result into a JSON-compatible dictionary.
        """

        return {
            "success": self.success,
            "faces": self.faces,
            "face_colors": self.face_colors,
            "confidence": self.confidence,
            "scanned_faces": self.scanned_faces,
            "missing_faces": self.missing_faces,
            "duplicate_faces": self.duplicate_faces,
            "color_counts": self.color_counts,
            "warnings": self.warnings,
            "error": self.error,
        }


# ============================================================================
# Cube Scan Session
# ============================================================================

class CubeScanSession:
    """
    Collects six Rubik's Cube face scans.

    Example:

        session = CubeScanSession()

        result = scanner.scan(image)

        session.add_scan(result)

        if session.is_complete():
            cube = session.build_result()
    """

    def __init__(
        self,
        scanner: CubeScanner | None = None,
    ) -> None:

        self.scanner = (
            scanner
            if scanner is not None
            else CubeScanner()
        )

        self._faces: dict[str, FaceScan] = {}

        self._history: list[str] = []


    # ========================================================================
    # Public API
    # ========================================================================

    def add_scan(
        self,
        result: ScanResult,
    ) -> bool:
        """
        Add a ScanResult to the session.

        Returns:

            True
                if the scan was accepted.

            False
                if the scan was rejected.
        """

        # --------------------------------------------------------------------
        # Basic result validation
        # --------------------------------------------------------------------

        if result is None:
            return False

        if not result.success:
            return False

        face_name = (
            result.face_name
        )

        face_color = (
            result.face_color
        )

        # --------------------------------------------------------------------
        # Validate detected face
        # --------------------------------------------------------------------

        if face_name not in FACE_NAMES:
            return False

        if face_color not in VALID_COLORS:
            return False

        # --------------------------------------------------------------------
        # Verify color → face mapping
        # --------------------------------------------------------------------

        expected_face = COLOR_TO_FACE.get(
            face_color
        )

        if expected_face != face_name:
            return False

        # --------------------------------------------------------------------
        # Validate 3x3 matrix
        # --------------------------------------------------------------------

        if not self._is_valid_face_matrix(
            result.colors
        ):
            return False

        # --------------------------------------------------------------------
        # Do not silently overwrite an existing face
        # --------------------------------------------------------------------

        if face_name in self._faces:
            return False

        # --------------------------------------------------------------------
        # Store face
        # --------------------------------------------------------------------

        face_scan = FaceScan(
            face_name=face_name,
            face_color=face_color,
            colors=[
                list(row)
                for row in result.colors
            ],
            confidence=float(
                result.confidence
            ),
            warnings=list(
                result.warnings or []
            ),
        )

        self._faces[
            face_name
        ] = face_scan

        self._history.append(
            face_name
        )

        return True


    def add_face(
        self,
        result: ScanResult,
    ) -> bool:
        """
        Alias for add_scan().
        """

        return self.add_scan(
            result
        )


    def scan_image(
        self,
        image,
    ) -> ScanResult:
        """
        Scan one image using the existing CubeScanner
        and automatically add it to the session if valid.
        """

        result = self.scanner.scan(
            image
        )

        if result.success:
            self.add_scan(
                result
            )

        return result


    def is_complete(
        self,
    ) -> bool:
        """
        Return True when all six cube faces
        have been scanned.
        """

        return len(
            self._faces
        ) == EXPECTED_FACES


    def scanned_count(
        self,
    ) -> int:
        """
        Return the number of unique faces scanned.
        """

        return len(
            self._faces
        )


    def remaining_count(
        self,
    ) -> int:
        """
        Return the number of faces still required.
        """

        return (
            EXPECTED_FACES
            - self.scanned_count()
        )


    def scanned_faces(
        self,
    ) -> list[str]:
        """
        Return scanned face names in standard cube order.
        """

        return [
            face
            for face in FACE_NAMES
            if face in self._faces
        ]


    def missing_faces(
        self,
    ) -> list[str]:
        """
        Return faces that have not yet been scanned.
        """

        return [
            face
            for face in FACE_NAMES
            if face not in self._faces
        ]


    def get_face(
        self,
        face_name: str,
    ) -> Optional[FaceScan]:
        """
        Get a previously scanned face.
        """

        return self._faces.get(
            face_name
        )


    def reset(
        self,
    ) -> None:
        """
        Clear the complete scan session.
        """

        self._faces.clear()
        self._history.clear()


    # ========================================================================
    # Result construction
    # ========================================================================

    def build_result(
        self,
    ) -> CubeScanResult:
        """
        Build a complete cube scan result.

        This performs global color-count validation.

        It does NOT yet perform cubie-level validation.
        """

        faces: dict[
            str,
            list[list[str]]
        ] = {}

        face_colors: dict[
            str,
            str
        ] = {}

        for face_name in FACE_NAMES:

            face = self._faces.get(
                face_name
            )

            if face is None:
                continue

            faces[
                face_name
            ] = [
                list(row)
                for row in face.colors
            ]

            face_colors[
                face_name
            ] = face.face_color

        scanned_faces = self.scanned_faces()

        missing_faces = self.missing_faces()

        duplicate_faces: list[str] = []

        warnings: list[str] = []

        # --------------------------------------------------------------------
        # Collect face warnings
        # --------------------------------------------------------------------

        for face_name in scanned_faces:

            face = self._faces[
                face_name
            ]

            for warning in face.warnings:

                warnings.append(
                    f"{face_name}: {warning}"
                )

        # --------------------------------------------------------------------
        # Calculate global color counts
        # --------------------------------------------------------------------

        color_counts = (
            self._calculate_color_counts()
        )

        # --------------------------------------------------------------------
        # Validate completeness
        # --------------------------------------------------------------------

        if not self.is_complete():

            return CubeScanResult(
                success=False,
                faces=faces,
                face_colors=face_colors,
                confidence=self._average_confidence(),
                scanned_faces=scanned_faces,
                missing_faces=missing_faces,
                duplicate_faces=duplicate_faces,
                color_counts=color_counts,
                warnings=warnings,
                error=(
                    "Cube scan is incomplete. "
                    f"Missing faces: "
                    f"{', '.join(missing_faces)}."
                ),
            )

        # --------------------------------------------------------------------
        # Validate color counts
        # --------------------------------------------------------------------

        invalid_color_counts = [
            color
            for color in COLORS
            if color_counts.get(
                color,
                0,
            ) != EXPECTED_STICKERS
        ]

        if invalid_color_counts:

            for color in invalid_color_counts:

                actual = color_counts.get(
                    color,
                    0,
                )

                warnings.append(
                    f"Color '{color}' appears "
                    f"{actual} time(s); expected 9."
                )

            return CubeScanResult(
                success=False,
                faces=faces,
                face_colors=face_colors,
                confidence=self._average_confidence(),
                scanned_faces=scanned_faces,
                missing_faces=missing_faces,
                duplicate_faces=duplicate_faces,
                color_counts=color_counts,
                warnings=warnings,
                error=(
                    "Invalid cube color counts."
                ),
            )

        # --------------------------------------------------------------------
        # Successful six-face collection
        # --------------------------------------------------------------------

        return CubeScanResult(
            success=True,
            faces=faces,
            face_colors=face_colors,
            confidence=self._average_confidence(),
            scanned_faces=scanned_faces,
            missing_faces=[],
            duplicate_faces=duplicate_faces,
            color_counts=color_counts,
            warnings=warnings,
            error=None,
        )


    # ========================================================================
    # Cube state
    # ========================================================================

    def build_cube_state(
        self,
    ) -> dict[str, list[list[str]]]:
        """
        Return the complete six-face color state.

        Face order:

            U
            R
            F
            D
            L
            B

        Raises RuntimeError if the session is incomplete
        or the color counts are invalid.
        """

        result = self.build_result()

        if not result.success:

            raise RuntimeError(
                result.error
                or "Cannot build cube state."
            )

        return {
            face: [
                list(row)
                for row in result.faces[face]
            ]
            for face in FACE_NAMES
        }


    def build_flat_state(
        self,
    ) -> list[str]:
        """
        Return all 54 stickers as a flat color list.

        Order:

            U[0..8]
            R[0..8]
            F[0..8]
            D[0..8]
            L[0..8]
            B[0..8]
        """

        cube_state = (
            self.build_cube_state()
        )

        stickers: list[str] = []

        for face in FACE_NAMES:

            matrix = cube_state[
                face
            ]

            for row in matrix:

                stickers.extend(
                    row
                )

        if len(stickers) != 54:

            raise RuntimeError(
                "Cube state must contain "
                "exactly 54 stickers."
            )

        return stickers


    # ========================================================================
    # Color counting
    # ========================================================================

    def _calculate_color_counts(
        self,
    ) -> dict[str, int]:
        """
        Count all colors across scanned faces.
        """

        counts = {
            color: 0
            for color in COLORS
        }

        for face in self._faces.values():

            for row in face.colors:

                for color in row:

                    normalized = (
                        str(color)
                        .strip()
                        .lower()
                    )

                    if normalized in counts:

                        counts[
                            normalized
                        ] += 1

        return counts


    # ========================================================================
    # Confidence
    # ========================================================================

    def _average_confidence(
        self,
    ) -> float:
        """
        Average confidence of all scanned faces.
        """

        if not self._faces:
            return 0.0

        total = sum(
            face.confidence
            for face in self._faces.values()
        )

        return max(
            0.0,
            min(
                1.0,
                total / len(
                    self._faces
                ),
            ),
        )


    # ========================================================================
    # Validation helpers
    # ========================================================================

    @staticmethod
    def _is_valid_face_matrix(
        colors: Any,
    ) -> bool:
        """
        Verify that a scanned face is exactly 3x3.
        """

        if not isinstance(
            colors,
            list,
        ):
            return False

        if len(colors) != GRID_SIZE:
            return False

        for row in colors:

            if not isinstance(
                row,
                list,
            ):
                return False

            if len(row) != GRID_SIZE:
                return False

            for color in row:

                if color not in VALID_COLORS:
                    return False

        return True


# ============================================================================
# Convenience function
# ============================================================================

def create_scan_session() -> CubeScanSession:
    """
    Create a new CubeScanSession.
    """

    return CubeScanSession()


# ============================================================================
# JSON helper
# ============================================================================

def cube_scan_result_json(
    result: CubeScanResult,
) -> str:
    """
    Convert a CubeScanResult to formatted JSON.
    """

    return json.dumps(
        result.to_dict(),
        indent=2,
    )


# ============================================================================
# CLI
# ============================================================================

def main() -> None:

    print(
        "CubeAI Scan Session"
    )

    print(
        "-------------------"
    )

    session = CubeScanSession()

    print()
    print(
        "Session created."
    )

    print(
        "Expected faces: "
        "U R F D L B"
    )

    print()

    # ------------------------------------------------------------------------
    # Demonstration only
    # ------------------------------------------------------------------------

    print(
        "This module is designed to be used "
        "by the webcam/UI pipeline."
    )

    print()

    print(
        "Current session:"
    )

    print(
        f"  Scanned: "
        f"{session.scanned_count()}/6"
    )

    print(
        f"  Missing: "
        f"{' '.join(session.missing_faces())}"
    )

    print()

    result = session.build_result()

    print(
        "Session status:"
    )

    print(
        f"  Complete: "
        f"{result.success}"
    )

    print(
        f"  Confidence: "
        f"{result.confidence:.2f}"
    )

    if result.error:

        print(
            f"  Error: "
            f"{result.error}"
        )

    print()

    print(
        "JSON:"
    )

    print(
        cube_scan_result_json(
            result
        )
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()