"""
CubeAI - Scanner

High-level vision pipeline for scanning one Rubik's Cube face.

Pipeline:

    input image/frame
          |
          v
    CubeDetector
          |
          v
    perspective-corrected cube face
          |
          v
    FaceDetector
          |
          v
    9 sticker regions
          |
          v
    robust BGR sampling
          |
          v
    ColorClassifier
          |
          v
    validated 3x3 color grid
          |
          v
    face identification

This module is intentionally independent from the webcam.

A webcam can later provide frames directly to:

    CubeScanner.scan(frame)

The scanner combines the individual vision components into
one reliable API.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any, Iterable, Optional

import cv2
import numpy as np


# ============================================================================
# Paths
# ============================================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VISION_DIR = CURRENT_DIR

COLOR_CLASSIFIER_DIR = os.path.abspath(
    os.path.join(
        CURRENT_DIR,
        "..",
        "color-classifier",
    )
)

if VISION_DIR not in sys.path:
    sys.path.insert(0, VISION_DIR)

if COLOR_CLASSIFIER_DIR not in sys.path:
    sys.path.insert(0, COLOR_CLASSIFIER_DIR)


# ============================================================================
# Imports
# ============================================================================

try:
    from cubeDetector import CubeDetector
except ImportError as exc:
    CubeDetector = None
    CUBE_DETECTOR_ERROR = str(exc)
else:
    CUBE_DETECTOR_ERROR = None


try:
    from faceDetector import FaceDetector
except ImportError as exc:
    FaceDetector = None
    FACE_DETECTOR_ERROR = str(exc)
else:
    FACE_DETECTOR_ERROR = None


try:
    from colorClassifier import classify_bgr
except ImportError as exc:
    classify_bgr = None
    COLOR_CLASSIFIER_ERROR = str(exc)
else:
    COLOR_CLASSIFIER_ERROR = None


# ============================================================================
# Constants
# ============================================================================

EXPECTED_STICKERS = 9
GRID_SIZE = 3

FACE_NAMES = (
    "U",
    "R",
    "F",
    "D",
    "L",
    "B",
)

MIN_COLOR_CONFIDENCE = 0.55

UNKNOWN_COLOR = "unknown"

VALID_COLORS = {
    "white",
    "yellow",
    "red",
    "orange",
    "green",
    "blue",
}


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


# ============================================================================
# Data structures
# ============================================================================

@dataclass
class StickerResult:
    """
    Result for one sticker.
    """

    row: int
    col: int
    color: str
    confidence: float
    bgr: tuple[int, int, int]


@dataclass
class ScanResult:
    """
    Complete result for one scanned cube face.
    """

    success: bool

    colors: list[list[str]]

    stickers: list[StickerResult]

    confidence: float

    error: Optional[str] = None

    warnings: list[str] | None = None

    detection_confidence: float = 0.0

    sticker_confidence: float = 0.0

    geometry_confidence: float = 0.0

    face_color: Optional[str] = None

    face_name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert result to JSON-compatible dictionary.
        """

        return {
            "success": self.success,
            "colors": self.colors,

            "stickers": [
                asdict(sticker)
                for sticker in self.stickers
            ],

            "confidence": self.confidence,

            "detection_confidence": (
                self.detection_confidence
            ),

            "sticker_confidence": (
                self.sticker_confidence
            ),

            "geometry_confidence": (
                self.geometry_confidence
            ),

            "face_color": self.face_color,

            "face_name": self.face_name,

            "warnings": self.warnings or [],

            "error": self.error,
        }


# ============================================================================
# Scanner
# ============================================================================

class CubeScanner:
    """
    High-level Rubik's Cube face scanner.

    The scanner combines:

        CubeDetector
            ↓
        FaceDetector
            ↓
        Sticker geometry validation
            ↓
        ColorClassifier
            ↓
        Face identification

    Input:

        OpenCV BGR image

    Output:

        ScanResult
    """

    def __init__(
        self,
        cube_detector: Any = None,
        face_detector: Any = None,
        min_color_confidence: float = MIN_COLOR_CONFIDENCE,
    ) -> None:

        self.cube_detector = (
            cube_detector
            if cube_detector is not None
            else CubeDetector()
            if CubeDetector is not None
            else None
        )

        self.face_detector = (
            face_detector
            if face_detector is not None
            else FaceDetector()
            if FaceDetector is not None
            else None
        )

        self.min_color_confidence = max(
            0.0,
            min(
                1.0,
                float(min_color_confidence),
            ),
        )


    # ========================================================================
    # Public API
    # ========================================================================

    def scan(
        self,
        image: np.ndarray,
    ) -> ScanResult:
        """
        Scan one Rubik's Cube face.
        """

        # --------------------------------------------------------------------
        # Validate input
        # --------------------------------------------------------------------

        validation_error = self._validate_image(
            image
        )

        if validation_error is not None:
            return self._failure(
                validation_error
            )

        try:

            # ================================================================
            # Step 1: Detect cube
            # ================================================================

            print(
                "Step 1: Detecting cube..."
            )

            cube_image, detection_confidence = (
                self._detect_cube(image)
            )

            if cube_image is None:
                raise RuntimeError(
                    "Cube detector returned no image."
                )

            cube_height, cube_width = (
                cube_image.shape[:2]
            )

            print(
                f"  Cube image: "
                f"{cube_width}x{cube_height}"
            )

            # ================================================================
            # Step 2: Detect stickers
            # ================================================================

            print(
                "Step 2: Detecting stickers..."
            )

            regions, detector_warnings = (
                self._detect_face(
                    cube_image
                )
            )

            print(
                f"  Detected regions: "
                f"{len(regions)}"
            )

            if len(regions) != EXPECTED_STICKERS:

                raise RuntimeError(
                    f"Expected {EXPECTED_STICKERS} "
                    f"stickers, found {len(regions)}."
                )

            # ================================================================
            # Step 2.5: Analyze sticker geometry
            # ================================================================

            geometry_confidence, geometry_warnings = (
                self._analyze_geometry(
                    regions,
                    cube_image.shape,
                )
            )

            warnings = []

            warnings.extend(
                detector_warnings
            )

            warnings.extend(
                geometry_warnings
            )

            # ================================================================
            # Step 2.6: Normalize sticker ordering
            # ================================================================

            regions = self._sort_regions(
                regions
            )

            # ================================================================
            # Step 3: Classify colors
            # ================================================================

            print(
                "Step 3: Classifying colors..."
            )

            stickers: list[StickerResult] = []

            for index, region in enumerate(regions):

                row = index // GRID_SIZE
                col = index % GRID_SIZE

                bgr = self._extract_bgr(
                    cube_image,
                    region,
                )

                color, confidence = self._classify(
                    bgr
                )

                color = self._normalize_color(
                    color
                )

                confidence = self._clamp_confidence(
                    confidence
                )

                sticker = StickerResult(
                    row=row,
                    col=col,
                    color=color,
                    confidence=confidence,
                    bgr=(
                        int(bgr[0]),
                        int(bgr[1]),
                        int(bgr[2]),
                    ),
                )

                stickers.append(
                    sticker
                )

                print(
                    f"  [{row},{col}] "
                    f"{color:<7} "
                    f"confidence={confidence:.2f} "
                    f"BGR={bgr}"
                )

            # ================================================================
            # Step 4: Build color matrix
            # ================================================================

            colors = self._build_color_matrix(
                stickers
            )

            # ================================================================
            # Step 5: Identify face from center
            # ================================================================

            face_color, face_name = (
                self._identify_face(
                    stickers
                )
            )

            print()

            print(
                f"  Detected face:"
            )

            print(
                f"    Color: {face_color}"
            )

            print(
                f"    Face:  {face_name}"
            )

            # ================================================================
            # Step 6: Calculate confidence
            # ================================================================

            sticker_confidence = (
                self._average_confidence(
                    stickers
                )
            )

            confidence = (
                self._calculate_confidence(
                    detection_confidence,
                    sticker_confidence,
                    geometry_confidence,
                )
            )

            # ================================================================
            # Step 7: Validate classifications
            # ================================================================

            color_warnings = (
                self._validate_colors(
                    stickers,
                    face_color,
                )
            )

            warnings.extend(
                color_warnings
            )

            # ================================================================
            # Step 8: Final success decision
            # ================================================================

            has_invalid_color = any(
                sticker.color not in VALID_COLORS
                for sticker in stickers
            )

            has_low_confidence = any(
                sticker.confidence
                < self.min_color_confidence
                for sticker in stickers
            )

            invalid_center = (
                face_color not in VALID_COLORS
                or face_name is None
            )

            success = (
                not has_invalid_color
                and not has_low_confidence
                and not invalid_center
            )

            if not success:

                error_messages: list[str] = []

                if has_invalid_color:

                    error_messages.append(
                        "One or more stickers "
                        "could not be classified."
                    )

                if has_low_confidence:

                    error_messages.append(
                        "One or more sticker "
                        "classifications have low "
                        "confidence."
                    )

                if invalid_center:

                    error_messages.append(
                        "The center sticker could not "
                        "identify a valid cube face."
                    )

                return ScanResult(
                    success=False,
                    colors=colors,
                    stickers=stickers,
                    confidence=confidence,
                    error=" ".join(
                        error_messages
                    ),
                    warnings=warnings,
                    detection_confidence=(
                        detection_confidence
                    ),
                    sticker_confidence=(
                        sticker_confidence
                    ),
                    geometry_confidence=(
                        geometry_confidence
                    ),
                    face_color=face_color,
                    face_name=face_name,
                )

            # ================================================================
            # Successful result
            # ================================================================

            return ScanResult(
                success=True,
                colors=colors,
                stickers=stickers,
                confidence=confidence,
                error=None,
                warnings=warnings,
                detection_confidence=(
                    detection_confidence
                ),
                sticker_confidence=(
                    sticker_confidence
                ),
                geometry_confidence=(
                    geometry_confidence
                ),
                face_color=face_color,
                face_name=face_name,
            )

        except Exception as exc:

            return self._failure(
                str(exc)
            )


    # ========================================================================
    # Input validation
    # ========================================================================

    @staticmethod
    def _validate_image(
        image: Any,
    ) -> Optional[str]:

        if image is None:
            return "Input image is empty."

        if not isinstance(
            image,
            np.ndarray,
        ):
            return (
                "Input must be an OpenCV "
                "NumPy image."
            )

        if image.size == 0:
            return (
                "Input image contains no pixels."
            )

        if image.ndim not in (2, 3):
            return (
                "Input image must have "
                "2 or 3 dimensions."
            )

        if image.ndim == 3:

            if image.shape[2] not in (1, 3, 4):
                return (
                    "Input image must have "
                    "1, 3, or 4 channels."
                )

        return None


    # ========================================================================
    # Cube detection
    # ========================================================================

    def _detect_cube(
        self,
        image: np.ndarray,
    ) -> tuple[np.ndarray, float]:

        if self.cube_detector is None:

            if CUBE_DETECTOR_ERROR:

                raise RuntimeError(
                    "CubeDetector is unavailable: "
                    f"{CUBE_DETECTOR_ERROR}"
                )

            raise RuntimeError(
                "CubeDetector is unavailable."
            )

        detector = self.cube_detector

        if not hasattr(
            detector,
            "detect",
        ):
            raise RuntimeError(
                "CubeDetector does not provide "
                "a detect() method."
            )

        try:

            result = detector.detect(
                image
            )

        except Exception as exc:

            raise RuntimeError(
                f"Cube detection failed: {exc}"
            ) from exc

        detection_confidence = 0.0

        # --------------------------------------------------------------------
        # CubeFace-like result
        # --------------------------------------------------------------------

        if hasattr(
            result,
            "warped",
        ):

            warped = result.warped

            if (
                isinstance(
                    warped,
                    np.ndarray,
                )
                and warped.size > 0
            ):

                if hasattr(
                    result,
                    "confidence",
                ):

                    detection_confidence = (
                        self._clamp_confidence(
                            result.confidence
                        )
                    )

                print(
                    "  Cube face detected!"
                )

                print(
                    f"  Detection confidence: "
                    f"{detection_confidence:.2f}"
                )

                print(
                    f"  Using warped face: "
                    f"{warped.shape[1]}x"
                    f"{warped.shape[0]}"
                )

                return (
                    warped,
                    detection_confidence,
                )

        # --------------------------------------------------------------------
        # Direct NumPy result
        # --------------------------------------------------------------------

        if isinstance(
            result,
            np.ndarray,
        ):

            if result.size == 0:

                raise RuntimeError(
                    "Cube detector returned "
                    "an empty image."
                )

            print(
                "  Cube face detected!"
            )

            print(
                f"  Cube image: "
                f"{result.shape[1]}x"
                f"{result.shape[0]}"
            )

            return (
                result,
                1.0,
            )

        # --------------------------------------------------------------------
        # Dictionary result
        # --------------------------------------------------------------------

        if isinstance(
            result,
            dict,
        ):

            if "confidence" in result:

                try:

                    detection_confidence = (
                        self._clamp_confidence(
                            result["confidence"]
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    detection_confidence = 0.0

            for key in (
                "warped",
                "warped_image",
                "image",
                "crop",
                "cropped",
                "cube",
                "roi",
            ):

                value = result.get(
                    key
                )

                if (
                    isinstance(
                        value,
                        np.ndarray,
                    )
                    and value.size > 0
                ):

                    print(
                        "  Cube face detected!"
                    )

                    print(
                        f"  Detection confidence: "
                        f"{detection_confidence:.2f}"
                    )

                    print(
                        f"  Using detector result: "
                        f"{key}"
                    )

                    return (
                        value,
                        detection_confidence,
                    )

        raise RuntimeError(
            "Cube detector did not return "
            "a usable warped cube face."
        )


    # ========================================================================
    # Face detection
    # ========================================================================

    def _detect_face(
        self,
        image: np.ndarray,
    ) -> tuple[list[Any], list[str]]:

        if self.face_detector is None:

            error = (
                FACE_DETECTOR_ERROR
                if FACE_DETECTOR_ERROR
                else "Unknown import error."
            )

            raise RuntimeError(
                "FaceDetector is unavailable: "
                f"{error}"
            )

        detector = self.face_detector

        if hasattr(
            detector,
            "detect",
        ):

            result = detector.detect(
                image
            )

        elif hasattr(
            detector,
            "detect_stickers",
        ):

            result = detector.detect_stickers(
                image
            )

        else:

            raise RuntimeError(
                "FaceDetector does not provide "
                "a supported detection method."
            )

        warnings: list[str] = []

        # --------------------------------------------------------------------
        # List / tuple
        # --------------------------------------------------------------------

        if isinstance(
            result,
            (list, tuple),
        ):

            return (
                list(result),
                warnings,
            )

        # --------------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------------

        if isinstance(
            result,
            dict,
        ):

            result_warnings = result.get(
                "warnings",
                [],
            )

            if isinstance(
                result_warnings,
                list,
            ):

                warnings.extend(
                    str(warning)
                    for warning in result_warnings
                )

            regions = result.get(
                "regions"
            )

            if regions is not None:

                return (
                    list(regions),
                    warnings,
                )

            stickers = result.get(
                "stickers"
            )

            if stickers is not None:

                return (
                    list(stickers),
                    warnings,
                )

        # --------------------------------------------------------------------
        # Object result with regions
        # --------------------------------------------------------------------

        if hasattr(
            result,
            "regions",
        ):

            object_warnings = getattr(
                result,
                "warnings",
                [],
            )

            if isinstance(
                object_warnings,
                list,
            ):

                warnings.extend(
                    str(warning)
                    for warning in object_warnings
                )

            return (
                list(result.regions),
                warnings,
            )

        # --------------------------------------------------------------------
        # Object result with stickers
        # --------------------------------------------------------------------

        if hasattr(
            result,
            "stickers",
        ):

            object_warnings = getattr(
                result,
                "warnings",
                [],
            )

            if isinstance(
                object_warnings,
                list,
            ):

                warnings.extend(
                    str(warning)
                    for warning in object_warnings
                )

            return (
                list(result.stickers),
                warnings,
            )

        raise RuntimeError(
            "Face detector returned "
            "an unsupported result."
        )


    # ========================================================================
    # Geometry analysis
    # ========================================================================

    def _analyze_geometry(
        self,
        regions: list[Any],
        image_shape: tuple[int, ...],
    ) -> tuple[float, list[str]]:

        """
        Analyze whether the detected stickers form a valid 3x3 grid.

        IMPORTANT:
            Do not calculate spacing from every adjacent X/Y coordinate.

            With 9 stickers, coordinates look roughly like:

                X: x1 x1 x1 x2 x2 x2 x3 x3 x3
                Y: y1 y2 y3 y1 y2 y3 y1 y2 y3

            A naive diff() therefore produces many tiny values.

        Instead, we:
            1. Extract all sticker centers.
            2. Cluster them into 3 columns and 3 rows.
            3. Measure spacing between column/row centers.
            4. Measure how well stickers align to those rows/columns.
            5. Measure sticker-size consistency.
            6. Measure whether the complete grid occupies a sensible
               portion of the detected cube face.

        This makes the geometry score independent of the absolute image size.
        """

        warnings: list[str] = []

        if len(regions) != EXPECTED_STICKERS:
            return (
                0.0,
                [
                    f"Expected {EXPECTED_STICKERS} sticker regions, "
                    f"found {len(regions)}."
                ],
            )

        # --------------------------------------------------------------------
        # Extract centers and sizes
        # --------------------------------------------------------------------

        centers: list[tuple[float, float]] = []
        sizes: list[tuple[float, float]] = []

        for region in regions:

            center = self._get_region_center(region)

            if center is None:
                continue

            centers.append(
                (
                    float(center[0]),
                    float(center[1]),
                )
            )

            size = self._get_region_size(region)

            if size is not None:
                sizes.append(
                    (
                        float(size[0]),
                        float(size[1]),
                    )
                )

        if len(centers) != EXPECTED_STICKERS:
            return (
                0.0,
                [
                    "Unable to determine all sticker centers."
                ],
            )

        points = np.asarray(
            centers,
            dtype=np.float32,
        )

        image_height, image_width = image_shape[:2]

        if image_width <= 0 or image_height <= 0:
            return (
                0.0,
                [
                    "Invalid cube image dimensions."
                ],
            )

        # --------------------------------------------------------------------
        # Cluster X coordinates into 3 columns
        #
        # Since exactly 9 stickers are expected, sorting the X coordinates
        # and grouping them into 3 groups of 3 is reliable.
        # --------------------------------------------------------------------

        x_sorted = sorted(
            float(point[0])
            for point in points
        )

        y_sorted = sorted(
            float(point[1])
            for point in points
        )

        x_columns = [
            x_sorted[0:3],
            x_sorted[3:6],
            x_sorted[6:9],
        ]

        y_rows = [
            y_sorted[0:3],
            y_sorted[3:6],
            y_sorted[6:9],
        ]

        column_centers = np.array(
            [
                float(np.mean(column))
                for column in x_columns
            ],
            dtype=np.float32,
        )

        row_centers = np.array(
            [
                float(np.mean(row))
                for row in y_rows
            ],
            dtype=np.float32,
        )

        # --------------------------------------------------------------------
        # Make sure the three columns and rows are actually separated.
        # --------------------------------------------------------------------

        column_spacing = np.diff(
            column_centers
        )

        row_spacing = np.diff(
            row_centers
        )

        if (
            len(column_spacing) != 2
            or len(row_spacing) != 2
        ):
            return (
                0.0,
                [
                    "Unable to estimate 3x3 grid spacing."
                ],
            )

        horizontal_spacing = float(
            np.median(column_spacing)
        )

        vertical_spacing = float(
            np.median(row_spacing)
        )

        if (
            horizontal_spacing <= 1.0
            or vertical_spacing <= 1.0
        ):
            return (
                0.0,
                [
                    "Sticker grid spacing is too small."
                ],
            )

        # --------------------------------------------------------------------
        # Spacing consistency
        #
        # A good cube grid should have approximately equal spacing:
        #
        #     column gap 1 ≈ column gap 2
        #     row gap 1    ≈ row gap 2
        # --------------------------------------------------------------------

        horizontal_spacing_variation = (
            abs(
                float(column_spacing[0])
                - float(column_spacing[1])
            )
            / horizontal_spacing
        )

        vertical_spacing_variation = (
            abs(
                float(row_spacing[0])
                - float(row_spacing[1])
            )
            / vertical_spacing
        )

        horizontal_spacing_score = max(
            0.0,
            1.0 - min(
                horizontal_spacing_variation,
                1.0,
            ),
        )

        vertical_spacing_score = max(
            0.0,
            1.0 - min(
                vertical_spacing_variation,
                1.0,
            ),
        )

        spacing_consistency_score = (
            horizontal_spacing_score
            + vertical_spacing_score
        ) / 2.0

        # --------------------------------------------------------------------
        # Alignment score
        #
        # Each sticker should be close to one of the three column centers
        # and one of the three row centers.
        #
        # This handles perspective/rotation much better than comparing raw
        # coordinate differences.
        # --------------------------------------------------------------------

        x_errors: list[float] = []
        y_errors: list[float] = []

        for x, y in points:

            nearest_column = float(
                np.min(
                    np.abs(
                        column_centers - x
                    )
                )
            )

            nearest_row = float(
                np.min(
                    np.abs(
                        row_centers - y
                    )
                )
            )

            x_errors.append(
                nearest_column
            )

            y_errors.append(
                nearest_row
            )

        mean_x_error = float(
            np.mean(x_errors)
        )

        mean_y_error = float(
            np.mean(y_errors)
        )

        # Normalize alignment error against grid spacing.
        normalized_x_error = (
            mean_x_error
            / max(
                horizontal_spacing,
                1.0,
            )
        )

        normalized_y_error = (
            mean_y_error
            / max(
                vertical_spacing,
                1.0,
            )
        )

        alignment_error = (
            normalized_x_error
            + normalized_y_error
        ) / 2.0

        alignment_score = max(
            0.0,
            1.0 - min(
                alignment_error * 3.0,
                1.0,
            ),
        )

        # --------------------------------------------------------------------
        # Sticker size consistency
        # --------------------------------------------------------------------

        size_score = 1.0

        if len(sizes) == EXPECTED_STICKERS:

            widths = np.asarray(
                [
                    size[0]
                    for size in sizes
                ],
                dtype=np.float32,
            )

            heights = np.asarray(
                [
                    size[1]
                    for size in sizes
                ],
                dtype=np.float32,
            )

            mean_width = float(
                np.mean(widths)
            )

            mean_height = float(
                np.mean(heights)
            )

            if mean_width > 0 and mean_height > 0:

                width_variation = (
                    float(np.std(widths))
                    / mean_width
                )

                height_variation = (
                    float(np.std(heights))
                    / mean_height
                )

                size_variation = (
                    width_variation
                    + height_variation
                ) / 2.0

                size_score = max(
                    0.0,
                    1.0 - min(
                        size_variation * 3.0,
                        1.0,
                    ),
                )

        # --------------------------------------------------------------------
        # Grid scale sanity check
        #
        # The distance between the first and last sticker centers should be
        # a meaningful portion of the detected cube face.
        #
        # This is relative to image dimensions, so it works for 300x300,
        # 600x600, 1000x1000, etc.
        # --------------------------------------------------------------------

        grid_width = (
            float(
                column_centers[-1]
                - column_centers[0]
            )
        )

        grid_height = (
            float(
                row_centers[-1]
                - row_centers[0]
            )
        )

        grid_width_ratio = (
            grid_width
            / max(
                float(image_width),
                1.0,
            )
        )

        grid_height_ratio = (
            grid_height
            / max(
                float(image_height),
                1.0,
            )
        )

        # A sticker grid should normally occupy a substantial portion of
        # the detected cube face.
        #
        # These are deliberately broad bounds because different detectors
        # may return different sticker margins.
        scale_score_x = 1.0

        if grid_width_ratio < 0.25:
            scale_score_x = 0.0
        elif grid_width_ratio < 0.40:
            scale_score_x = (
                grid_width_ratio - 0.25
            ) / 0.15
        elif grid_width_ratio <= 0.95:
            scale_score_x = 1.0
        else:
            scale_score_x = max(
                0.0,
                1.0 - (
                    grid_width_ratio - 0.95
                ) / 0.20,
            )

        scale_score_y = 1.0

        if grid_height_ratio < 0.25:
            scale_score_y = 0.0
        elif grid_height_ratio < 0.40:
            scale_score_y = (
                grid_height_ratio - 0.25
            ) / 0.15
        elif grid_height_ratio <= 0.95:
            scale_score_y = 1.0
        else:
            scale_score_y = max(
                0.0,
                1.0 - (
                    grid_height_ratio - 0.95
                ) / 0.20,
            )

        scale_score = (
            scale_score_x
            + scale_score_y
        ) / 2.0

        # --------------------------------------------------------------------
        # Warnings
        # --------------------------------------------------------------------

        # Use a relative threshold rather than an absolute pixel threshold.
        if horizontal_spacing < image_width * 0.05:
            warnings.append(
                "Sticker columns are unusually close together."
            )

        if vertical_spacing < image_height * 0.05:
            warnings.append(
                "Sticker rows are unusually close together."
            )

        if horizontal_spacing_variation > 0.25:
            warnings.append(
                "Horizontal sticker spacing is inconsistent."
            )

        if vertical_spacing_variation > 0.25:
            warnings.append(
                "Vertical sticker spacing is inconsistent."
            )

        if alignment_score < 0.60:
            warnings.append(
                "Sticker centers do not align cleanly "
                "to a 3x3 grid."
            )

        if size_score < 0.60:
            warnings.append(
                "Sticker sizes are inconsistent."
            )

        if scale_score < 0.60:
            warnings.append(
                "Sticker grid occupies an unusual portion "
                "of the detected cube face."
            )

        # --------------------------------------------------------------------
        # Final geometry confidence
        #
        # Alignment is the strongest signal because a valid 3x3 sticker
        # layout should have clean row/column structure.
        # --------------------------------------------------------------------

        geometry_confidence = (
            spacing_consistency_score * 0.35
            + alignment_score * 0.35
            + size_score * 0.15
            + scale_score * 0.15
        )

        geometry_confidence = (
            self._clamp_confidence(
                geometry_confidence
            )
        )

        print(
            f"  Geometry confidence: "
            f"{geometry_confidence:.2f}"
        )

        print(
            f"  Grid spacing: "
            f"{horizontal_spacing:.1f} x "
            f"{vertical_spacing:.1f}"
        )

        print(
            f"  Grid alignment: "
            f"{alignment_score:.2f}"
        )

        return (
            geometry_confidence,
            warnings,
        )


    # ========================================================================
    # Region ordering
    # ========================================================================

    def _sort_regions(
        self,
        regions: list[Any],
    ) -> list[Any]:

        """
        Normalize sticker order into:

            0 1 2
            3 4 5
            6 7 8

        Ordering is based on sticker centers rather than
        detector output order.
        """

        if len(regions) != EXPECTED_STICKERS:
            return regions

        items = []

        for region in regions:

            center = self._get_region_center(
                region
            )

            if center is None:

                # No geometry available.
                # Preserve detector order.
                return regions

            x, y = center

            items.append(
                (
                    float(x),
                    float(y),
                    region,
                )
            )

        # --------------------------------------------------------------------
        # Sort by Y first.
        # --------------------------------------------------------------------

        items.sort(
            key=lambda item: item[1]
        )

        y_values = np.array(
            [
                item[1]
                for item in items
            ],
            dtype=np.float32,
        )

        # Estimate normal row spacing.
        y_diffs = np.diff(
            y_values
        )

        positive_diffs = y_diffs[
            y_diffs > 1
        ]

        if len(positive_diffs) == 0:

            return regions

        row_spacing = float(
            np.median(
                positive_diffs
            )
        )

        # Adaptive threshold.
        threshold = max(
            10.0,
            row_spacing * 0.45,
        )

        rows: list[
            list[tuple[float, float, Any]]
        ] = []

        for item in items:

            x, y, region = item

            best_row = None
            best_distance = float("inf")

            for index, row in enumerate(rows):

                row_y = float(
                    np.mean(
                        [
                            existing[1]
                            for existing in row
                        ]
                    )
                )

                distance = abs(
                    y - row_y
                )

                if (
                    distance < threshold
                    and distance < best_distance
                ):

                    best_distance = distance
                    best_row = index

            if best_row is None:

                rows.append(
                    [item]
                )

            else:

                rows[best_row].append(
                    item
                )

        # --------------------------------------------------------------------
        # The ideal result is exactly 3 rows of 3.
        # --------------------------------------------------------------------

        if len(rows) != GRID_SIZE:

            return self._fallback_grid_sort(
                items
            )

        for row in rows:

            if len(row) != GRID_SIZE:

                return self._fallback_grid_sort(
                    items
                )

        # --------------------------------------------------------------------
        # Sort rows vertically.
        # --------------------------------------------------------------------

        rows.sort(
            key=lambda row: np.mean(
                [
                    item[1]
                    for item in row
                ]
            )
        )

        ordered: list[Any] = []

        for row in rows:

            row.sort(
                key=lambda item: item[0]
            )

            ordered.extend(
                item[2]
                for item in row
            )

        if len(ordered) != EXPECTED_STICKERS:

            return regions

        return ordered


    @staticmethod
    def _fallback_grid_sort(
        items: list[
            tuple[float, float, Any]
        ],
    ) -> list[Any]:

        """
        Fallback ordering when adaptive row clustering
        cannot cleanly produce 3 rows.

        Since exactly 9 regions are expected, this uses
        Y-order chunks of 3 and then sorts each chunk by X.
        """

        ordered = sorted(
            items,
            key=lambda item: (
                item[1],
                item[0],
            ),
        )

        rows = [
            ordered[0:3],
            ordered[3:6],
            ordered[6:9],
        ]

        result: list[Any] = []

        for row in rows:

            row.sort(
                key=lambda item: item[0]
            )

            result.extend(
                item[2]
                for item in row
            )

        return result


    # ========================================================================
    # Region center
    # ========================================================================

    def _get_region_center(
        self,
        region: Any,
    ) -> Optional[tuple[int, int]]:

        if isinstance(
            region,
            dict,
        ):

            if "center" in region:

                center = region["center"]

                return (
                    int(center[0]),
                    int(center[1]),
                )

            if (
                "center_x" in region
                and "center_y" in region
            ):

                return (
                    int(region["center_x"]),
                    int(region["center_y"]),
                )

            if (
                "x" in region
                and "y" in region
            ):

                if (
                    "width" in region
                    and "height" in region
                ):

                    return (
                        int(
                            region["x"]
                            + region["width"] / 2
                        ),
                        int(
                            region["y"]
                            + region["height"] / 2
                        ),
                    )

                if (
                    "w" in region
                    and "h" in region
                ):

                    return (
                        int(
                            region["x"]
                            + region["w"] / 2
                        ),
                        int(
                            region["y"]
                            + region["h"] / 2
                        ),
                    )

        if (
            hasattr(region, "center_x")
            and hasattr(region, "center_y")
        ):

            return (
                int(region.center_x),
                int(region.center_y),
            )

        if (
            hasattr(region, "x")
            and hasattr(region, "y")
            and hasattr(region, "width")
            and hasattr(region, "height")
        ):

            return (
                int(
                    region.x
                    + region.width / 2
                ),
                int(
                    region.y
                    + region.height / 2
                ),
            )

        if (
            hasattr(region, "x")
            and hasattr(region, "y")
            and hasattr(region, "w")
            and hasattr(region, "h")
        ):

            return (
                int(
                    region.x
                    + region.w / 2
                ),
                int(
                    region.y
                    + region.h / 2
                ),
            )

        return None


    # ========================================================================
    # Region size
    # ========================================================================

    @staticmethod
    def _get_region_size(
        region: Any,
    ) -> Optional[tuple[float, float]]:

        if isinstance(
            region,
            dict,
        ):

            if (
                "width" in region
                and "height" in region
            ):

                return (
                    float(region["width"]),
                    float(region["height"]),
                )

            if (
                "w" in region
                and "h" in region
            ):

                return (
                    float(region["w"]),
                    float(region["h"]),
                )

        if (
            hasattr(region, "width")
            and hasattr(region, "height")
        ):

            return (
                float(region.width),
                float(region.height),
            )

        if (
            hasattr(region, "w")
            and hasattr(region, "h")
        ):

            return (
                float(region.w),
                float(region.h),
            )

        return None


    # ========================================================================
    # BGR extraction
    # ========================================================================

    def _extract_bgr(
        self,
        image: np.ndarray,
        region: Any,
    ) -> tuple[int, int, int]:

        # --------------------------------------------------------------------
        # Tuple/list: x, y, w, h
        # --------------------------------------------------------------------

        if isinstance(
            region,
            (list, tuple),
        ):

            if len(region) == 4:

                x, y, w, h = [
                    int(value)
                    for value in region
                ]

                return self._sample_region(
                    image,
                    x,
                    y,
                    w,
                    h,
                )

        # --------------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------------

        if isinstance(
            region,
            dict,
        ):

            if all(
                key in region
                for key in (
                    "x",
                    "y",
                    "width",
                    "height",
                )
            ):

                return self._sample_region(
                    image,
                    int(region["x"]),
                    int(region["y"]),
                    int(region["width"]),
                    int(region["height"]),
                )

            if all(
                key in region
                for key in (
                    "x",
                    "y",
                    "w",
                    "h",
                )
            ):

                return self._sample_region(
                    image,
                    int(region["x"]),
                    int(region["y"]),
                    int(region["w"]),
                    int(region["h"]),
                )

            if all(
                key in region
                for key in (
                    "x1",
                    "y1",
                    "x2",
                    "y2",
                )
            ):

                x1 = int(region["x1"])
                y1 = int(region["y1"])
                x2 = int(region["x2"])
                y2 = int(region["y2"])

                return self._sample_region(
                    image,
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1,
                )

            if "bgr" in region:

                bgr = region["bgr"]

                return (
                    int(bgr[0]),
                    int(bgr[1]),
                    int(bgr[2]),
                )

            if "center" in region:

                center = region["center"]

                return self._sample_center(
                    image,
                    int(center[0]),
                    int(center[1]),
                )

        # --------------------------------------------------------------------
        # Object: x, y, width, height
        # --------------------------------------------------------------------

        if all(
            hasattr(region, key)
            for key in (
                "x",
                "y",
                "width",
                "height",
            )
        ):

            return self._sample_region(
                image,
                int(region.x),
                int(region.y),
                int(region.width),
                int(region.height),
            )

        # --------------------------------------------------------------------
        # Object: x, y, w, h
        # --------------------------------------------------------------------

        if all(
            hasattr(region, key)
            for key in (
                "x",
                "y",
                "w",
                "h",
            )
        ):

            return self._sample_region(
                image,
                int(region.x),
                int(region.y),
                int(region.w),
                int(region.h),
            )

        # --------------------------------------------------------------------
        # Object: x1, y1, x2, y2
        # --------------------------------------------------------------------

        if all(
            hasattr(region, key)
            for key in (
                "x1",
                "y1",
                "x2",
                "y2",
            )
        ):

            x1 = int(region.x1)
            y1 = int(region.y1)
            x2 = int(region.x2)
            y2 = int(region.y2)

            return self._sample_region(
                image,
                x1,
                y1,
                x2 - x1,
                y2 - y1,
            )

        # --------------------------------------------------------------------
        # Object center
        # --------------------------------------------------------------------

        if all(
            hasattr(region, key)
            for key in (
                "center_x",
                "center_y",
            )
        ):

            return self._sample_center(
                image,
                int(region.center_x),
                int(region.center_y),
            )

        raise RuntimeError(
            f"Unsupported sticker region: "
            f"{region!r}"
        )


    # ========================================================================
    # Sample region
    # ========================================================================

    @staticmethod
    def _sample_region(
        image: np.ndarray,
        x: int,
        y: int,
        w: int,
        h: int,
    ) -> tuple[int, int, int]:

        height, width = image.shape[:2]

        x1 = max(
            0,
            x,
        )

        y1 = max(
            0,
            y,
        )

        x2 = min(
            width,
            x + w,
        )

        y2 = min(
            height,
            y + h,
        )

        if x2 <= x1 or y2 <= y1:

            raise RuntimeError(
                "Sticker region is outside "
                "image bounds."
            )

        roi = image[
            y1:y2,
            x1:x2,
        ]

        if roi.size == 0:

            raise RuntimeError(
                "Sticker region contains "
                "no pixels."
            )

        # --------------------------------------------------------------------
        # Ignore border pixels.
        #
        # This reduces black gaps, borders and reflections.
        # --------------------------------------------------------------------

        rh, rw = roi.shape[:2]

        margin_x = max(
            1,
            int(rw * 0.20),
        )

        margin_y = max(
            1,
            int(rh * 0.20),
        )

        if (
            rw > margin_x * 2
            and rh > margin_y * 2
        ):

            roi = roi[
                margin_y:rh - margin_y,
                margin_x:rw - margin_x,
            ]

        # --------------------------------------------------------------------
        # Median sampling.
        # --------------------------------------------------------------------

        pixels = roi.reshape(
            -1,
            3,
        )

        median = np.median(
            pixels,
            axis=0,
        )

        return (
            int(round(median[0])),
            int(round(median[1])),
            int(round(median[2])),
        )


    # ========================================================================
    # Sample center
    # ========================================================================

    @staticmethod
    def _sample_center(
        image: np.ndarray,
        x: int,
        y: int,
        radius: int = 8,
    ) -> tuple[int, int, int]:

        height, width = image.shape[:2]

        x1 = max(
            0,
            x - radius,
        )

        y1 = max(
            0,
            y - radius,
        )

        x2 = min(
            width,
            x + radius + 1,
        )

        y2 = min(
            height,
            y + radius + 1,
        )

        roi = image[
            y1:y2,
            x1:x2,
        ]

        if roi.size == 0:

            raise RuntimeError(
                "Sticker center is outside "
                "image bounds."
            )

        pixels = roi.reshape(
            -1,
            3,
        )

        median = np.median(
            pixels,
            axis=0,
        )

        return (
            int(round(median[0])),
            int(round(median[1])),
            int(round(median[2])),
        )


    # ========================================================================
    # Color classification
    # ========================================================================

    @staticmethod
    def _classify(
        bgr: tuple[int, int, int],
    ) -> tuple[str, float]:

        if classify_bgr is None:

            error = (
                COLOR_CLASSIFIER_ERROR
                if COLOR_CLASSIFIER_ERROR
                else "Unknown import error."
            )

            raise RuntimeError(
                "Color classifier is unavailable: "
                f"{error}"
            )

        b, g, r = bgr

        result = classify_bgr(
            b,
            g,
            r,
        )

        # --------------------------------------------------------------------
        # ColorResult-like object
        # --------------------------------------------------------------------

        if hasattr(
            result,
            "color",
        ):

            return (
                str(result.color),
                float(
                    getattr(
                        result,
                        "confidence",
                        0.0,
                    )
                ),
            )

        # --------------------------------------------------------------------
        # Tuple
        # --------------------------------------------------------------------

        if isinstance(
            result,
            tuple,
        ):

            if len(result) >= 2:

                return (
                    str(result[0]),
                    float(result[1]),
                )

        # --------------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------------

        if isinstance(
            result,
            dict,
        ):

            color = result.get(
                "color",
                result.get(
                    "label",
                    UNKNOWN_COLOR,
                ),
            )

            confidence = result.get(
                "confidence",
                0.0,
            )

            return (
                str(color),
                float(confidence),
            )

        # --------------------------------------------------------------------
        # Label-only result
        # --------------------------------------------------------------------

        return (
            str(result),
            0.0,
        )


    # ========================================================================
    # Color normalization
    # ========================================================================

    @staticmethod
    def _normalize_color(
        color: Any,
    ) -> str:

        if color is None:
            return UNKNOWN_COLOR

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

        normalized = aliases.get(
            normalized,
            normalized,
        )

        if normalized not in VALID_COLORS:
            return UNKNOWN_COLOR

        return normalized


    # ========================================================================
    # Face identification
    # ========================================================================

    @staticmethod
    def _identify_face(
        stickers: list[StickerResult],
    ) -> tuple[Optional[str], Optional[str]]:

        if len(stickers) != EXPECTED_STICKERS:

            return (
                None,
                None,
            )

        center = stickers[4]

        face_color = (
            CubeScanner._normalize_color(
                center.color
            )
        )

        face_name = COLOR_TO_FACE.get(
            face_color
        )

        return (
            face_color
            if face_color in VALID_COLORS
            else None,
            face_name,
        )


    # ========================================================================
    # Color validation
    # ========================================================================

    @staticmethod
    def _validate_colors(
        stickers: list[StickerResult],
        face_color: Optional[str],
    ) -> list[str]:

        warnings: list[str] = []

        # --------------------------------------------------------------------
        # Invalid colors
        # --------------------------------------------------------------------

        invalid = [
            sticker.color
            for sticker in stickers
            if sticker.color not in VALID_COLORS
        ]

        if invalid:

            warnings.append(
                "Invalid color classification detected."
            )

        # --------------------------------------------------------------------
        # Low confidence
        # --------------------------------------------------------------------

        low_confidence = [
            (
                sticker.row,
                sticker.col,
                sticker.color,
                sticker.confidence,
            )
            for sticker in stickers
            if sticker.confidence
            < MIN_COLOR_CONFIDENCE
        ]

        if low_confidence:

            warnings.append(
                f"{len(low_confidence)} sticker(s) "
                "have low classification confidence."
            )

        # --------------------------------------------------------------------
        # Center validation
        # --------------------------------------------------------------------

        if face_color not in VALID_COLORS:

            warnings.append(
                "The center sticker could not "
                "identify a valid face."
            )

        # --------------------------------------------------------------------
        # IMPORTANT:
        #
        # We intentionally DO NOT warn if the center color
        # appears only once.
        #
        # A scrambled cube can legitimately have only one
        # sticker of a particular color on a face.
        #
        # We also DO NOT require a 3x3 face to contain only
        # one color. A scrambled face naturally contains
        # multiple colors.
        # --------------------------------------------------------------------

        # --------------------------------------------------------------------
        # Dominant-color warning
        #
        # Only warn if ALL/ALMOST ALL stickers have the same
        # color. This can indicate a blank/solved-like face,
        # but is not itself an error.
        # --------------------------------------------------------------------

        color_counts: dict[str, int] = {}

        for sticker in stickers:

            color_counts[sticker.color] = (
                color_counts.get(
                    sticker.color,
                    0,
                )
                + 1
            )

        if color_counts:

            dominant_color = max(
                color_counts,
                key=color_counts.get,
            )

            dominant_count = (
                color_counts[
                    dominant_color
                ]
            )

            if dominant_count == 9:

                warnings.append(
                    "All stickers were classified "
                    "as the same color."
                )

            elif dominant_count == 8:

                warnings.append(
                    "Nearly all stickers were "
                    "classified as the same color."
                )

        return warnings


    # ========================================================================
    # Confidence
    # ========================================================================

    @staticmethod
    def _average_confidence(
        stickers: list[StickerResult],
    ) -> float:

        if not stickers:
            return 0.0

        return float(
            sum(
                sticker.confidence
                for sticker in stickers
            )
            / len(stickers)
        )


    @staticmethod
    def _calculate_confidence(
        detection_confidence: float,
        sticker_confidence: float,
        geometry_confidence: float,
    ) -> float:

        """
        Combine:

            35% cube detection
            50% sticker color classification
            15% sticker geometry
        """

        detection_confidence = (
            CubeScanner._clamp_confidence(
                detection_confidence
            )
        )

        sticker_confidence = (
            CubeScanner._clamp_confidence(
                sticker_confidence
            )
        )

        geometry_confidence = (
            CubeScanner._clamp_confidence(
                geometry_confidence
            )
        )

        confidence = (
            detection_confidence * 0.35
            + sticker_confidence * 0.50
            + geometry_confidence * 0.15
        )

        return CubeScanner._clamp_confidence(
            confidence
        )


    # ========================================================================
    # Confidence helper
    # ========================================================================

    @staticmethod
    def _clamp_confidence(
        value: Any,
    ) -> float:

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
            ),
        )


    # ========================================================================
    # Color matrix
    # ========================================================================

    @staticmethod
    def _build_color_matrix(
        stickers: list[StickerResult],
    ) -> list[list[str]]:

        if len(stickers) != EXPECTED_STICKERS:

            raise RuntimeError(
                "Cannot build 3x3 matrix from "
                f"{len(stickers)} stickers."
            )

        return [
            [
                stickers[
                    row * GRID_SIZE + col
                ].color
                for col in range(GRID_SIZE)
            ]
            for row in range(GRID_SIZE)
        ]


    # ========================================================================
    # Failure helper
    # ========================================================================

    @staticmethod
    def _failure(
        error: str,
    ) -> ScanResult:

        return ScanResult(
            success=False,
            colors=[],
            stickers=[],
            confidence=0.0,
            error=error,
            warnings=[],
            detection_confidence=0.0,
            sticker_confidence=0.0,
            geometry_confidence=0.0,
            face_color=None,
            face_name=None,
        )


# ============================================================================
# Convenience function
# ============================================================================

def scan_image(
    image_path: str,
) -> ScanResult:

    """
    Scan a single image from disk.
    """

    if not image_path:

        return CubeScanner()._failure(
            "Image path cannot be empty."
        )

    image = cv2.imread(
        image_path,
        cv2.IMREAD_COLOR,
    )

    if image is None:

        return CubeScanner()._failure(
            f"Could not load image: {image_path}"
        )

    scanner = CubeScanner()

    return scanner.scan(
        image
    )


# ============================================================================
# JSON output
# ============================================================================

def scan_image_json(
    image_path: str,
) -> str:

    """
    Scan an image and return JSON.
    """

    result = scan_image(
        image_path
    )

    return json.dumps(
        result.to_dict(),
        indent=2,
    )


def scan_cube_images(
    image_paths: Iterable[str],
) -> Any:
    """Scan six face images and return a validated engine CubeState result."""

    from cubeStateBuilder import CubeStateBuildResult, CubeStateBuilder
    from scanSession import CubeScanSession

    paths = list(image_paths)

    if len(paths) != len(FACE_NAMES):
        return CubeStateBuildResult(
            success=False,
            errors=[
                f"Expected 6 face images, received {len(paths)}."
            ],
            missing_faces=list(FACE_NAMES),
        )

    session = CubeScanSession()

    for path in paths:
        result = scan_image(path)

        if not result.success:
            return CubeStateBuildResult(
                success=False,
                scanned_faces=session.scanned_faces(),
                missing_faces=session.missing_faces(),
                errors=[
                    f"Failed to scan '{path}': {result.error}"
                ],
            )

        if not session.add_scan(result):
            return CubeStateBuildResult(
                success=False,
                scanned_faces=session.scanned_faces(),
                missing_faces=session.missing_faces(),
                errors=[
                    f"Scan for '{path}' was rejected by the scan session."
                ],
            )

    return CubeStateBuilder().build(session)


# ============================================================================
# CLI
# ============================================================================

def main() -> None:

    print(
        "CubeAI Scanner"
    )

    print(
        "--------------"
    )

    if len(sys.argv) == 7:

        result = scan_cube_images(
            sys.argv[1:]
        )

        print()
        print(
            "CubeState pipeline:",
            "SUCCESS" if result.success else "FAILED",
        )

        if result.errors:
            for error in result.errors:
                print(f"  ERROR: {error}")

        print()
        print(json.dumps(result.to_dict(), indent=2))
        return

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "  py ai\\vision\\scanner.py <image>"
        )

        print()

        print(
            "Example:"
        )

        print(
            "  py ai\\vision\\scanner.py "
            "test-images\\cube-color.jpg"
        )

        print()

        print(
            "  py ai\\vision\\scanner.py "
            "<U-image> <R-image> <F-image> "
            "<D-image> <L-image> <B-image>"
        )

        return

    image_path = sys.argv[1]

    print(
        f"Image: {image_path}"
    )

    print()

    result = scan_image(
        image_path
    )

    print()

    # ------------------------------------------------------------------------
    # Failed scan
    # ------------------------------------------------------------------------

    if not result.success:

        print(
            "Scan failed:"
        )

        print(
            f"  {result.error}"
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

        return

    # ------------------------------------------------------------------------
    # Successful scan
    # ------------------------------------------------------------------------

    print(
        "Scan successful!"
    )

    print()

    print(
        "Detected face:"
    )

    print(
        f"  Color: {result.face_color}"
    )

    print(
        f"  Face:  {result.face_name}"
    )

    print()

    print(
        "Detected colors:"
    )

    for row in result.colors:

        print(
            "  " + " ".join(row)
        )

    print()

    print(
        f"Detection confidence: "
        f"{result.detection_confidence:.2f}"
    )

    print(
        f"Sticker confidence:   "
        f"{result.sticker_confidence:.2f}"
    )

    print(
        f"Geometry confidence:  "
        f"{result.geometry_confidence:.2f}"
    )

    print(
        f"Overall confidence:   "
        f"{result.confidence:.2f}"
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