"""
CubeAI - Cube Scanner

High-level vision pipeline for scanning one Rubik's Cube face.

Pipeline:

    input image
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

This module intentionally does NOT handle webcam capture.

A webcam can later provide frames directly to:

    CubeScanner.scan(frame)

The scanner combines the existing vision components into
one stable API for the cube-state engine.
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

COLOR_CLASSIFIER_DIR = os.path.abspath(
    os.path.join(
        CURRENT_DIR,
        "..",
        "color-classifier",
    )
)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

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

GRID_SIZE = 3
EXPECTED_STICKERS = GRID_SIZE * GRID_SIZE

MIN_COLOR_CONFIDENCE = 0.55

VALID_COLORS = {
    "white",
    "yellow",
    "red",
    "orange",
    "green",
    "blue",
}

UNKNOWN_COLOR = "unknown"

# The scanner only scans ONE face.
#
# Therefore we do not require exactly one of each color.
#
# We only use this to detect suspicious output such as
# all 9 stickers being classified as the same color.
MAX_DOMINANT_COLOR_RATIO = 8 / 9

# Border ignored when sampling sticker colors.
STICKER_MARGIN_RATIO = 0.20


# ============================================================================
# Data structures
# ============================================================================

@dataclass
class StickerResult:
    """
    Classification result for one sticker.
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

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the scan result into a JSON-compatible dictionary.
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
            "warnings": self.warnings or [],
            "error": self.error,
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Convert the scan result directly to JSON.
        """

        return json.dumps(
            self.to_dict(),
            indent=indent,
        )


# ============================================================================
# Cube Scanner
# ============================================================================

class CubeScanner:
    """
    High-level Rubik's Cube face scanner.

    Pipeline:

        CubeDetector
             ↓
        warped cube face
             ↓
        FaceDetector
             ↓
        9 sticker regions
             ↓
        ColorClassifier
             ↓
        ScanResult

    The scanner operates on OpenCV BGR images.
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
            else (
                CubeDetector()
                if CubeDetector is not None
                else None
            )
        )

        self.face_detector = (
            face_detector
            if face_detector is not None
            else (
                FaceDetector()
                if FaceDetector is not None
                else None
            )
        )

        self.min_color_confidence = float(
            min_color_confidence
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

        Parameters
        ----------
        image:
            OpenCV BGR image.

        Returns
        -------
        ScanResult
            Structured result containing:

                - 3x3 color matrix
                - individual sticker results
                - detection confidence
                - classification confidence
                - overall confidence
                - warnings/errors
        """

        validation_error = self._validate_image(
            image
        )

        if validation_error is not None:
            return self._failure(
                validation_error
            )

        try:

            # ================================================================
            # STEP 1
            # Cube detection
            # ================================================================

            print(
                "Step 1: Detecting cube..."
            )

            cube_image, detection_confidence = (
                self._detect_cube(image)
            )

            print(
                f"  Cube image: "
                f"{cube_image.shape[1]}x"
                f"{cube_image.shape[0]}"
            )

            # ================================================================
            # STEP 2
            # Sticker / face detection
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
            # STEP 2.5
            # Normalize sticker ordering
            # ================================================================

            regions = self._sort_regions(
                regions
            )

            # ================================================================
            # STEP 3
            # Color classification
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

                color, confidence = (
                    self._classify(bgr)
                )

                stickers.append(
                    StickerResult(
                        row=row,
                        col=col,
                        color=color,
                        confidence=float(
                            confidence
                        ),
                        bgr=(
                            int(bgr[0]),
                            int(bgr[1]),
                            int(bgr[2]),
                        ),
                    )
                )

            # ================================================================
            # STEP 4
            # Build 3x3 matrix
            # ================================================================

            colors = self._build_color_matrix(
                stickers
            )

            # ================================================================
            # STEP 5
            # Confidence
            # ================================================================

            sticker_confidence = (
                self._average_confidence(
                    stickers
                )
            )

            overall_confidence = (
                self._calculate_confidence(
                    detection_confidence,
                    sticker_confidence,
                )
            )

            # ================================================================
            # STEP 6
            # Validate classification
            # ================================================================

            warnings = self._validate_scan(
                stickers
            )

            # ================================================================
            # STEP 7
            # Final success decision
            # ================================================================

            invalid_colors = [
                sticker
                for sticker in stickers
                if sticker.color not in VALID_COLORS
            ]

            low_confidence = [
                sticker
                for sticker in stickers
                if (
                    sticker.confidence
                    < self.min_color_confidence
                )
            ]

            success = (
                len(invalid_colors) == 0
                and len(low_confidence) == 0
            )

            if not success:

                errors: list[str] = []

                if invalid_colors:

                    errors.append(
                        f"{len(invalid_colors)} "
                        "sticker(s) have invalid "
                        "color classification."
                    )

                if low_confidence:

                    errors.append(
                        f"{len(low_confidence)} "
                        "sticker(s) have low "
                        "classification confidence."
                    )

                return ScanResult(
                    success=False,
                    colors=colors,
                    stickers=stickers,
                    confidence=overall_confidence,
                    error=" ".join(errors),
                    warnings=warnings,
                    detection_confidence=(
                        detection_confidence
                    ),
                    sticker_confidence=(
                        sticker_confidence
                    ),
                )

            # ================================================================
            # SUCCESS
            # ================================================================

            return ScanResult(
                success=True,
                colors=colors,
                stickers=stickers,
                confidence=overall_confidence,
                error=None,
                warnings=warnings,
                detection_confidence=(
                    detection_confidence
                ),
                sticker_confidence=(
                    sticker_confidence
                ),
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

            if image.shape[2] not in (
                1,
                3,
                4,
            ):
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

            error = (
                CUBE_DETECTOR_ERROR
                or "CubeDetector unavailable."
            )

            raise RuntimeError(
                f"CubeDetector is unavailable: "
                f"{error}"
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
        # CubeFace object
        #
        # Current cubeDetector.py returns:
        #
        #     result.warped
        #     result.confidence
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
                        self._safe_confidence(
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
    # Face / sticker detection
    # ========================================================================

    def _detect_face(
        self,
        image: np.ndarray,
    ) -> list[Any]:

        if self.face_detector is None:

            error = (
                FACE_DETECTOR_ERROR
                or "FaceDetector unavailable."
            )

            raise RuntimeError(
                f"FaceDetector is unavailable: "
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
            ):

                value = result.get(
                    key
                )

                if value is not None:

                    return list(value)

        raise RuntimeError(
            "Face detector returned "
            "an unsupported result."
        )

    # ========================================================================
    # Region ordering
    # ========================================================================

    def _sort_regions(
        self,
        regions: list[Any],
    ) -> list[Any]:

        """
        Normalize sticker regions into:

            0 1 2
            3 4 5
            6 7 8

        FaceDetector currently already produces an ordered grid,
        but scanner.py should not blindly depend on that behavior.
        """

        centers: list[
            tuple[float, float, Any]
        ] = []

        for region in regions:

            center = self._get_region_center(
                region
            )

            if center is None:

                # No geometric information.
                # Preserve detector ordering.
                return regions

            x, y = center

            centers.append(
                (
                    float(x),
                    float(y),
                    region,
                )
            )

        if len(centers) != EXPECTED_STICKERS:
            return regions

        # --------------------------------------------------------------------
        # Sort by Y.
        # --------------------------------------------------------------------

        centers.sort(
            key=lambda item: item[1]
        )

        # --------------------------------------------------------------------
        # Estimate row spacing.
        # --------------------------------------------------------------------

        ys = [
            item[1]
            for item in centers
        ]

        y_min = min(ys)
        y_max = max(ys)

        row_tolerance = max(
            20.0,
            (y_max - y_min) * 0.20,
        )

        rows: list[
            list[tuple[float, float, Any]]
        ] = []

        # --------------------------------------------------------------------
        # Cluster into rows.
        # --------------------------------------------------------------------

        for item in centers:

            _, y, _ = item

            target_row = None

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
                    distance < row_tolerance
                    and distance < best_distance
                ):

                    target_row = row
                    best_distance = distance

            if target_row is None:

                rows.append(
                    [item]
                )

            else:

                target_row.append(
                    item
                )

        # --------------------------------------------------------------------
        # We expect exactly 3 rows.
        # --------------------------------------------------------------------

        if len(rows) != GRID_SIZE:

            # Fallback based on normalized coordinates.
            return self._fallback_grid_sort(
                centers
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

            if len(row) != GRID_SIZE:

                return self._fallback_grid_sort(
                    centers
                )

            ordered.extend(
                item[2]
                for item in row
            )

        if len(ordered) != EXPECTED_STICKERS:
            return regions

        return ordered

    # ========================================================================
    # Region center
    # ========================================================================

    @staticmethod
    def _get_region_center(
        region: Any,
    ) -> Optional[tuple[float, float]]:

        # --------------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------------

        if isinstance(
            region,
            dict,
        ):

            if "center" in region:

                center = region["center"]

                if len(center) >= 2:

                    return (
                        float(center[0]),
                        float(center[1]),
                    )

            if (
                "center_x" in region
                and "center_y" in region
            ):

                return (
                    float(region["center_x"]),
                    float(region["center_y"]),
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
                        float(
                            region["x"]
                            + region["width"] / 2
                        ),
                        float(
                            region["y"]
                            + region["height"] / 2
                        ),
                    )

                if (
                    "w" in region
                    and "h" in region
                ):

                    return (
                        float(
                            region["x"]
                            + region["w"] / 2
                        ),
                        float(
                            region["y"]
                            + region["h"] / 2
                        ),
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

                return (
                    (
                        float(region["x1"])
                        + float(region["x2"])
                    ) / 2,
                    (
                        float(region["y1"])
                        + float(region["y2"])
                    ) / 2,
                )

        # --------------------------------------------------------------------
        # Object: center_x / center_y
        # --------------------------------------------------------------------

        if (
            hasattr(region, "center_x")
            and hasattr(region, "center_y")
        ):

            return (
                float(region.center_x),
                float(region.center_y),
            )

        # --------------------------------------------------------------------
        # Object: x / y / width / height
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

            return (
                float(
                    region.x
                    + region.width / 2
                ),
                float(
                    region.y
                    + region.height / 2
                ),
            )

        # --------------------------------------------------------------------
        # Object: x / y / w / h
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

            return (
                float(
                    region.x
                    + region.w / 2
                ),
                float(
                    region.y
                    + region.h / 2
                ),
            )

        # --------------------------------------------------------------------
        # Object: x1 / y1 / x2 / y2
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

            return (
                (
                    float(region.x1)
                    + float(region.x2)
                ) / 2,
                (
                    float(region.y1)
                    + float(region.y2)
                ) / 2,
            )

        return None

    # ========================================================================
    # Fallback region sorting
    # ========================================================================

    @staticmethod
    def _fallback_grid_sort(
        centers: list[
            tuple[float, float, Any]
        ],
    ) -> list[Any]:

        """
        Fallback ordering for a 3x3 sticker grid.

        Uses normalized coordinates and sorts primarily
        by Y and secondarily by X.
        """

        ordered = sorted(
            centers,
            key=lambda item: (
                item[1],
                item[0],
            ),
        )

        # If there are exactly 9 regions, split them
        # into 3 groups of 3 after Y sorting.
        if len(ordered) == EXPECTED_STICKERS:

            rows = [
                ordered[0:3],
                ordered[3:6],
                ordered[6:9],
            ]

            rows.sort(
                key=lambda row: np.mean(
                    [
                        item[1]
                        for item in row
                    ]
                )
            )

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

        return [
            item[2]
            for item in ordered
        ]

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

                return self._sample_region(
                    image,
                    int(region["x1"]),
                    int(region["y1"]),
                    int(region["x2"])
                    - int(region["x1"]),
                    int(region["y2"])
                    - int(region["y1"]),
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

            return self._sample_region(
                image,
                int(region.x1),
                int(region.y1),
                int(region.x2 - region.x1),
                int(region.y2 - region.y1),
            )

        # --------------------------------------------------------------------
        # Object: center_x / center_y
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
    # Sample sticker region
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
        # Remove the outer 20%.
        #
        # This matches the sampling strategy used during our
        # previous vision work and reduces black gaps / borders.
        # --------------------------------------------------------------------

        rh, rw = roi.shape[:2]

        margin_x = max(
            1,
            int(rw * STICKER_MARGIN_RATIO),
        )

        margin_y = max(
            1,
            int(rh * STICKER_MARGIN_RATIO),
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
        # Median is more robust than mean against:
        #
        # - reflections
        # - shadows
        # - black borders
        # - small segmentation errors
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

        if x2 <= x1 or y2 <= y1:

            raise RuntimeError(
                "Sticker center is outside "
                "image bounds."
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
                or "ColorClassifier unavailable."
            )

            raise RuntimeError(
                f"Color classifier is unavailable: "
                f"{error}"
            )

        b, g, r = bgr

        result = classify_bgr(
            b,
            g,
            r,
        )

        # --------------------------------------------------------------------
        # ColorResult
        # --------------------------------------------------------------------

        if hasattr(
            result,
            "color",
        ):

            return (
                str(result.color),
                float(result.confidence),
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
        # Label only
        # --------------------------------------------------------------------

        return (
            str(result),
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
    # Validation
    # ========================================================================

    def _validate_scan(
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

            warnings.append(
                f"{len(invalid)} sticker(s) "
                "have an invalid color."
            )

        # --------------------------------------------------------------------
        # Low confidence
        # --------------------------------------------------------------------

        low_confidence = [
            sticker
            for sticker in stickers
            if (
                sticker.confidence
                < self.min_color_confidence
            )
        ]

        if low_confidence:

            warnings.append(
                f"{len(low_confidence)} sticker(s) "
                "have low classification confidence."
            )

        # --------------------------------------------------------------------
        # Color distribution
        #
        # This is only a warning because we are scanning
        # one face, not the entire cube.
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

            dominant_count = color_counts[
                dominant_color
            ]

            if (
                dominant_count
                >= MAX_DOMINANT_COLOR_RATIO
                * EXPECTED_STICKERS
            ):

                warnings.append(
                    "Nearly all stickers were "
                    "classified as the same color."
                )

        # --------------------------------------------------------------------
        # Center sticker warning
        #
        # The center is important because it identifies
        # the face color in the future cube-state engine.
        # --------------------------------------------------------------------

        if len(stickers) == EXPECTED_STICKERS:

            center = stickers[4]

            if center.color not in VALID_COLORS:

                warnings.append(
                    "Center sticker has an invalid "
                    "color classification."
                )

            if (
                center.confidence
                < self.min_color_confidence
            ):

                warnings.append(
                    "Center sticker has low "
                    "classification confidence."
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

        """
        Combine geometric and color confidence.

        Color classification receives slightly more weight
        because the resulting sticker colors are eventually
        consumed by the cube-state engine.
        """

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

            value = float(value)

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
            error=str(error),
            warnings=[],
            detection_confidence=0.0,
            sticker_confidence=0.0,
        )


# ============================================================================
# Convenience API
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


def scan_image_json(
    image_path: str,
) -> str:

    """
    Scan an image and return JSON.
    """

    return scan_image(
        image_path
    ).to_json()


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
            "  py ai\\vision\\cubeScanner.py <image>"
        )

        print()

        print(
            "Example:"
        )

        print(
            "  py ai\\vision\\cubeScanner.py "
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

    # ========================================================================
    # Failed scan
    # ========================================================================

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
            result.to_json()
        )

        return

    # ========================================================================
    # Successful scan
    # ========================================================================

    print(
        "Scan successful!"
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
        result.to_json()
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    main()