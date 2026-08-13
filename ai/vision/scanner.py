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
    ColorClassifier
          |
          v
    validated 3x3 color grid
          |
          v
    ScanResult
          |
          v
    CubeState.from_scan_results()

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
from dataclasses import asdict, dataclass
from typing import Any, Optional

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

# Maximum allowed distance from the expected normalized
# row position when clustering sticker centers.
ROW_CLUSTER_RATIO = 0.35

# Minimum acceptable normalized distance between neighboring
# sticker centers.
MIN_GRID_SPACING_RATIO = 0.20

# Maximum acceptable normalized distance between adjacent
# sticker centers.
MAX_GRID_SPACING_RATIO = 0.65

# Border ignored when sampling sticker colors.
ROI_MARGIN_RATIO = 0.20


# ============================================================================
# Data structures
# ============================================================================

@dataclass
class StickerResult:
    """
    Result for one sticker.

    row / col describe its normalized 3x3 position.
    """

    row: int
    col: int
    color: str
    confidence: float
    bgr: tuple[int, int, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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

    face_color: Optional[str] = None

    face_name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "colors": self.colors,
            "stickers": [
                asdict(sticker)
                for sticker in self.stickers
            ],
            "confidence": self.confidence,
            "detection_confidence": self.detection_confidence,
            "sticker_confidence": self.sticker_confidence,
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

    Combines:

        CubeDetector
            ↓
        FaceDetector
            ↓
        ColorClassifier

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

        self.min_color_confidence = float(
            max(
                0.0,
                min(
                    1.0,
                    min_color_confidence,
                ),
            )
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
        # Step 0: Validate image
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

            print(
                f"  Detection confidence: "
                f"{detection_confidence:.2f}"
            )

            # ================================================================
            # Step 2: Detect stickers
            # ================================================================

            print(
                "Step 2: Detecting stickers..."
            )

            regions = self._detect_face(
                cube_image
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
            # Step 2.5: Validate sticker geometry
            # ================================================================

            geometry_warnings = (
                self._validate_region_geometry(
                    cube_image,
                    regions,
                )
            )

            if geometry_warnings:
                print(
                    "  Geometry warnings:"
                )

                for warning in geometry_warnings:
                    print(
                        f"    - {warning}"
                    )

            # ================================================================
            # Step 2.6: Normalize sticker ordering
            # ================================================================

            regions = self._sort_regions(
                regions,
                cube_image.shape[:2],
            )

            if len(regions) != EXPECTED_STICKERS:
                raise RuntimeError(
                    "Could not normalize the detected "
                    "stickers into a 3x3 grid."
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

                stickers.append(
                    StickerResult(
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
            # Step 5: Determine face identity
            # ================================================================

            center_sticker = stickers[4]

            face_color = center_sticker.color

            face_name = self._color_to_face(
                face_color
            )

            # ================================================================
            # Step 6: Calculate confidence
            # ================================================================

            sticker_confidence = (
                self._average_confidence(
                    stickers
                )
            )

            confidence = self._calculate_confidence(
                detection_confidence,
                sticker_confidence,
            )

            # ================================================================
            # Step 7: Validate classification
            # ================================================================

            warnings = self._validate_colors(
                stickers
            )

            warnings.extend(
                geometry_warnings
            )

            # ================================================================
            # Step 8: Final success decision
            # ================================================================

            invalid_stickers = [
                sticker
                for sticker in stickers
                if sticker.color not in VALID_COLORS
            ]

            low_confidence_stickers = [
                sticker
                for sticker in stickers
                if sticker.confidence
                < self.min_color_confidence
            ]

            center_invalid = (
                face_color not in VALID_COLORS
            )

            errors: list[str] = []

            if invalid_stickers:
                errors.append(
                    f"{len(invalid_stickers)} sticker(s) "
                    "could not be classified."
                )

            if low_confidence_stickers:
                errors.append(
                    f"{len(low_confidence_stickers)} "
                    "sticker(s) have low classification "
                    "confidence."
                )

            if center_invalid:
                errors.append(
                    "Center sticker could not be "
                    "identified as a valid cube color."
                )

            success = not errors

            if not success:

                return ScanResult(
                    success=False,
                    colors=colors,
                    stickers=stickers,
                    confidence=confidence,
                    error=" ".join(errors),
                    warnings=warnings,
                    detection_confidence=(
                        detection_confidence
                    ),
                    sticker_confidence=(
                        sticker_confidence
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

        height, width = image.shape[:2]

        if height < 30 or width < 30:
            return (
                "Input image is too small "
                "for reliable cube scanning."
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
        # Object result
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

                detection_confidence = (
                    self._safe_confidence(
                        getattr(
                            result,
                            "confidence",
                            1.0,
                        )
                    )
                )

                print(
                    "  Cube face detected!"
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

            detection_confidence = (
                self._safe_confidence(
                    result.get(
                        "confidence",
                        0.0,
                    )
                )
            )

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
                        f"  Detector result: "
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
    ) -> list[Any]:

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

        try:

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

        except Exception as exc:

            raise RuntimeError(
                f"Sticker detection failed: {exc}"
            ) from exc

        # --------------------------------------------------------------------
        # List / tuple
        # --------------------------------------------------------------------

        if isinstance(
            result,
            (list, tuple),
        ):
            return list(result)

        # --------------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------------

        if isinstance(
            result,
            dict,
        ):

            for key in (
                "regions",
                "stickers",
                "detections",
                "boxes",
            ):

                values = result.get(
                    key
                )

                if values is not None:
                    return list(values)

        raise RuntimeError(
            "Face detector returned "
            "an unsupported result."
        )

    # ========================================================================
    # Region geometry validation
    # ========================================================================

    def _validate_region_geometry(
        self,
        image: np.ndarray,
        regions: list[Any],
    ) -> list[str]:

        warnings: list[str] = []

        if len(regions) != EXPECTED_STICKERS:
            return warnings

        centers = []

        for region in regions:

            center = self._get_region_center(
                region
            )

            if center is None:
                warnings.append(
                    "One or more sticker regions "
                    "do not expose spatial coordinates."
                )
                return warnings

            centers.append(center)

        # --------------------------------------------------------------------
        # Duplicate center detection
        # --------------------------------------------------------------------

        for i in range(len(centers)):

            for j in range(i + 1, len(centers)):

                dx = centers[i][0] - centers[j][0]
                dy = centers[i][1] - centers[j][1]

                distance = (
                    (dx * dx + dy * dy)
                    ** 0.5
                )

                if distance < 10:

                    warnings.append(
                        "Two sticker detections are "
                        "extremely close together."
                    )

                    return warnings

        # --------------------------------------------------------------------
        # Check approximate spacing
        # --------------------------------------------------------------------

        height, width = image.shape[:2]

        normalized = [
            (
                x / max(width, 1),
                y / max(height, 1),
            )
            for x, y in centers
        ]

        # Find unique x/y spread.
        xs = sorted(
            point[0]
            for point in normalized
        )

        ys = sorted(
            point[1]
            for point in normalized
        )

        x_gaps = [
            xs[i + 1] - xs[i]
            for i in range(len(xs) - 1)
        ]

        y_gaps = [
            ys[i + 1] - ys[i]
            for i in range(len(ys) - 1)
        ]

        if not x_gaps or not y_gaps:
            return warnings

        median_x_gap = float(
            np.median(x_gaps)
        )

        median_y_gap = float(
            np.median(y_gaps)
        )

        if median_x_gap < 0.03:
            warnings.append(
                "Sticker columns are unusually "
                "close together."
            )

        if median_y_gap < 0.03:
            warnings.append(
                "Sticker rows are unusually "
                "close together."
            )

        return warnings

    # ========================================================================
    # Region ordering
    # ========================================================================

    def _sort_regions(
        self,
        regions: list[Any],
        image_shape: tuple[int, int],
    ) -> list[Any]:

        """
        Normalize sticker order into:

            0 1 2
            3 4 5
            6 7 8

        Uses spatial centers instead of relying on the
        detector's output order.
        """

        if len(regions) != EXPECTED_STICKERS:
            return regions

        centers = []

        for region in regions:

            center = self._get_region_center(
                region
            )

            if center is None:
                # No spatial information.
                # Preserve detector order.
                return regions

            x, y = center

            centers.append(
                (
                    float(x),
                    float(y),
                    region,
                )
            )

        height, width = image_shape

        # --------------------------------------------------------------------
        # Estimate vertical spacing.
        # --------------------------------------------------------------------

        sorted_y = sorted(
            item[1]
            for item in centers
        )

        y_differences = [
            sorted_y[i + 1] - sorted_y[i]
            for i in range(
                len(sorted_y) - 1
            )
        ]

        positive_y_differences = [
            value
            for value in y_differences
            if value > 1
        ]

        if positive_y_differences:

            median_spacing = float(
                np.median(
                    positive_y_differences
                )
            )

        else:

            median_spacing = (
                height / 3.0
            )

        row_threshold = max(
            10.0,
            median_spacing
            * ROW_CLUSTER_RATIO,
        )

        # --------------------------------------------------------------------
        # Cluster centers into rows.
        # --------------------------------------------------------------------

        centers.sort(
            key=lambda item: item[1]
        )

        rows: list[
            list[tuple[float, float, Any]]
        ] = []

        for item in centers:

            x, y, region = item

            best_row = None
            best_distance = float("inf")

            for row in rows:

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
                    distance < row_threshold
                    and distance < best_distance
                ):

                    best_row = row
                    best_distance = distance

            if best_row is None:

                rows.append(
                    [item]
                )

            else:

                best_row.append(
                    item
                )

        # --------------------------------------------------------------------
        # We expect exactly 3 rows.
        # --------------------------------------------------------------------

        if len(rows) != GRID_SIZE:

            # More robust fallback:
            # divide sorted centers into three groups
            # of three.
            rows = [
                centers[0:3],
                centers[3:6],
                centers[6:9],
            ]

        # --------------------------------------------------------------------
        # Every row must contain exactly 3 stickers.
        # --------------------------------------------------------------------

        if any(
            len(row) != GRID_SIZE
            for row in rows
        ):

            return regions

        # --------------------------------------------------------------------
        # Sort rows vertically.
        # --------------------------------------------------------------------

        rows.sort(
            key=lambda row: float(
                np.mean(
                    [
                        item[1]
                        for item in row
                    ]
                )
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

    # ========================================================================
    # Region center extraction
    # ========================================================================

    def _get_region_center(
        self,
        region: Any,
    ) -> Optional[tuple[int, int]]:

        # --------------------------------------------------------------------
        # Tuple / list
        # --------------------------------------------------------------------

        if isinstance(
            region,
            (list, tuple),
        ):

            if len(region) == 4:

                x, y, w, h = [
                    float(value)
                    for value in region
                ]

                return (
                    int(
                        x + w / 2
                    ),
                    int(
                        y + h / 2
                    ),
                )

        # --------------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------------

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

        # --------------------------------------------------------------------
        # Object
        # --------------------------------------------------------------------

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

                if len(bgr) < 3:
                    raise RuntimeError(
                        "BGR value must contain "
                        "three channels."
                    )

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
            "Unsupported sticker region: "
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

        if w <= 0 or h <= 0:
            raise RuntimeError(
                "Sticker region has invalid dimensions."
            )

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
        # Ignore sticker borders.
        # --------------------------------------------------------------------

        rh, rw = roi.shape[:2]

        margin_x = max(
            1,
            int(
                rw * ROI_MARGIN_RATIO
            ),
        )

        margin_y = max(
            1,
            int(
                rh * ROI_MARGIN_RATIO
            ),
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
        # Median is robust against reflections,
        # shadows and small artifacts.
        # --------------------------------------------------------------------

        pixels = roi.reshape(
            -1,
            roi.shape[-1],
        )

        if pixels.shape[1] == 1:

            value = float(
                np.median(pixels)
            )

            return (
                int(value),
                int(value),
                int(value),
            )

        if pixels.shape[1] >= 3:

            median = np.median(
                pixels[:, :3],
                axis=0,
            )

            return (
                int(round(median[0])),
                int(round(median[1])),
                int(round(median[2])),
            )

        raise RuntimeError(
            "Unsupported image channel format."
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

        if (
            x < 0
            or x >= width
            or y < 0
            or y >= height
        ):
            raise RuntimeError(
                "Sticker center is outside "
                "image bounds."
            )

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
                "Sticker center contains "
                "no pixels."
            )

        pixels = roi.reshape(
            -1,
            roi.shape[-1],
        )

        if pixels.shape[1] == 1:

            value = float(
                np.median(pixels)
            )

            return (
                int(value),
                int(value),
                int(value),
            )

        median = np.median(
            pixels[:, :3],
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

        try:

            result = classify_bgr(
                b,
                g,
                r,
            )

        except Exception as exc:

            raise RuntimeError(
                f"Color classification failed: {exc}"
            ) from exc

        # --------------------------------------------------------------------
        # ColorResult
        # --------------------------------------------------------------------

        if hasattr(
            result,
            "color",
        ):

            color = str(
                result.color
            )

            confidence = (
                CubeScanner._safe_confidence(
                    getattr(
                        result,
                        "confidence",
                        0.0,
                    )
                )
            )

            return (
                color.lower(),
                confidence,
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
                    str(
                        result[0]
                    ).lower(),
                    CubeScanner._safe_confidence(
                        result[1]
                    ),
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
                str(
                    color
                ).lower(),
                CubeScanner._safe_confidence(
                    confidence
                ),
            )

        # --------------------------------------------------------------------
        # Label-only result
        # --------------------------------------------------------------------

        return (
            str(result).lower(),
            0.0,
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
    # Face mapping
    # ========================================================================

    @staticmethod
    def _color_to_face(
        color: str,
    ) -> Optional[str]:

        mapping = {
            "white": "U",
            "red": "R",
            "green": "F",
            "yellow": "D",
            "orange": "L",
            "blue": "B",
        }

        return mapping.get(
            color.lower()
        )

    # ========================================================================
    # Color validation
    # ========================================================================

    def _validate_colors(
        self,
        stickers: list[StickerResult],
    ) -> list[str]:

        warnings: list[str] = []

        # --------------------------------------------------------------------
        # Invalid colors
        # --------------------------------------------------------------------

        invalid = [
            sticker
            for sticker in stickers
            if sticker.color not in VALID_COLORS
        ]

        if invalid:

            positions = ", ".join(
                f"({s.row},{s.col})"
                for s in invalid
            )

            warnings.append(
                "Invalid color classification at "
                f"{positions}."
            )

        # --------------------------------------------------------------------
        # Low confidence
        # --------------------------------------------------------------------

        low_confidence = [
            sticker
            for sticker in stickers
            if sticker.confidence
            < self.min_color_confidence
        ]

        if low_confidence:

            positions = ", ".join(
                f"({s.row},{s.col})"
                for s in low_confidence
            )

            warnings.append(
                f"{len(low_confidence)} sticker(s) "
                "have low classification confidence "
                f"at {positions}."
            )

        # --------------------------------------------------------------------
        # Color count information
        #
        # We intentionally DO NOT require nine stickers
        # of the center color.
        #
        # This is one face of a cube, not the whole cube.
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

        # --------------------------------------------------------------------
        # Detect suspicious all-one-color result.
        # --------------------------------------------------------------------

        if color_counts:

            dominant_color = max(
                color_counts,
                key=color_counts.get,
            )

            dominant_count = color_counts[
                dominant_color
            ]

            if dominant_count == EXPECTED_STICKERS:

                warnings.append(
                    "All nine stickers were classified "
                    f"as {dominant_color}."
                )

            elif dominant_count >= 8:

                warnings.append(
                    "Nearly all stickers were "
                    "classified as the same color."
                )

        # --------------------------------------------------------------------
        # Center should normally be the dominant face color.
        # --------------------------------------------------------------------

        center = stickers[4].color

        if (
            center in VALID_COLORS
            and color_counts.get(center, 0) == 1
        ):

            warnings.append(
                "The center color appears only once "
                "on this scanned face."
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
    ) -> float:

        detection_confidence = (
            CubeScanner._safe_confidence(
                detection_confidence
            )
        )

        sticker_confidence = (
            CubeScanner._safe_confidence(
                sticker_confidence
            )
        )

        return float(
            (
                detection_confidence
                * 0.40
            )
            + (
                sticker_confidence
                * 0.60
            )
        )

    @staticmethod
    def _safe_confidence(
        value: Any,
    ) -> float:

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

        if not np.isfinite(value):
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

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

        return CubeScanner._failure(
            "Image path cannot be empty."
        )

    image = cv2.imread(
        image_path,
        cv2.IMREAD_COLOR,
    )

    if image is None:

        return CubeScanner._failure(
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
            "Scan failed."
        )

        print(
            f"  Error: {result.error}"
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
        f"  Color: "
        f"{result.face_color}"
    )

    print(
        f"  Face:  "
        f"{result.face_name}"
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