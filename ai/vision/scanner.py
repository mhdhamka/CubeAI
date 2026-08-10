
"""
CubeAI Scanner

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

This module is intentionally independent from the webcam.

A webcam can later provide frames directly to:

    CubeScanner.scan(frame)

The scanner is responsible for combining the individual
vision components into one reliable API.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
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

# Colors should not be considered valid if they fall outside
# the known Rubik's Cube color set.
INVALID_COLORS = {
    UNKNOWN_COLOR,
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
            "detection_confidence": self.detection_confidence,
            "sticker_confidence": self.sticker_confidence,
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
            Structured scan result.
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
            # Step 2.5: Normalize sticker ordering
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

                stickers.append(
                    StickerResult(
                        row=row,
                        col=col,
                        color=color,
                        confidence=float(confidence),
                        bgr=(
                            int(bgr[0]),
                            int(bgr[1]),
                            int(bgr[2]),
                        ),
                    )
                )

            # ================================================================
            # Step 4: Build color matrix
            # ================================================================

            colors = self._build_color_matrix(
                stickers
            )

            # ================================================================
            # Step 5: Calculate confidence
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
            # Step 6: Validate classification
            # ================================================================

            warnings = self._validate_colors(
                stickers
            )

            # ================================================================
            # Step 7: Final success decision
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

            success = (
                not has_invalid_color
                and not has_low_confidence
            )

            if not success:

                error_messages = []

                if has_invalid_color:

                    error_messages.append(
                        "One or more stickers "
                        "could not be classified."
                    )

                if has_low_confidence:

                    error_messages.append(
                        "One or more sticker "
                        "classifications have low confidence."
                    )

                return ScanResult(
                    success=False,
                    colors=colors,
                    stickers=stickers,
                    confidence=confidence,
                    error=" ".join(error_messages),
                    warnings=warnings,
                    detection_confidence=(
                        detection_confidence
                    ),
                    sticker_confidence=(
                        sticker_confidence
                    ),
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
        # CubeFace result
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

                    detection_confidence = float(
                        result.confidence
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

                    detection_confidence = float(
                        result["confidence"]
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

            regions = result.get(
                "regions"
            )

            if regions is not None:

                return list(regions)

            stickers = result.get(
                "stickers"
            )

            if stickers is not None:

                return list(stickers)

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
        Normalize sticker order into:

            0 1 2
            3 4 5
            6 7 8

        FaceDetector normally already returns this order,
        but scanner should not depend on that assumption.
        """

        centers: list[
            tuple[int, int, Any]
        ] = []

        for region in regions:

            center = self._get_region_center(
                region
            )

            if center is None:

                # If no spatial information exists,
                # preserve detector order.
                return regions

            x, y = center

            centers.append(
                (
                    int(x),
                    int(y),
                    region,
                )
            )

        # Sort vertically first.
        centers.sort(
            key=lambda item: item[1]
        )

        rows: list[
            list[tuple[int, int, Any]]
        ] = []

        # --------------------------------------------------------------------
        # Cluster the 9 centers into 3 rows.
        # --------------------------------------------------------------------

        for item in centers:

            x, y, region = item

            placed = False

            for row in rows:

                row_y = np.mean(
                    [
                        existing[1]
                        for existing in row
                    ]
                )

                if abs(y - row_y) < 80:

                    row.append(
                        item
                    )

                    placed = True
                    break

            if not placed:

                rows.append(
                    [item]
                )

        # --------------------------------------------------------------------
        # If clustering failed, use a simple y/x sort.
        # --------------------------------------------------------------------

        if len(rows) != GRID_SIZE:

            return sorted(
                regions,
                key=lambda region: (
                    self._get_region_center(
                        region
                    ) or (0, 0)
                )[1]
            )

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


    def _get_region_center(
        self,
        region: Any,
    ) -> Optional[tuple[int, int]]:

        # --------------------------------------------------------------------
        # center explicitly supplied
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
        # object center
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
        # The current FaceDetector gives regions around 116x116.
        # A 20% margin leaves the actual sticker center,
        # reducing influence from black gaps and borders.
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
        # Median is more robust than mean against small reflections,
        # shadows and remaining border pixels.
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

        # ColorResult
        if hasattr(
            result,
            "color",
        ):

            return (
                str(result.color),
                float(result.confidence),
            )

        # Tuple
        if isinstance(
            result,
            tuple,
        ):

            if len(result) >= 2:

                return (
                    str(result[0]),
                    float(result[1]),
                )

        # Dictionary
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

        # Label-only result
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
                stickers[row * GRID_SIZE + col].color
                for col in range(GRID_SIZE)
            ]
            for row in range(GRID_SIZE)
        ]


    # ========================================================================
    # Color validation
    # ========================================================================

    @staticmethod
    def _validate_colors(
        stickers: list[StickerResult],
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
        # Low confidence stickers
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
        # Color count information
        #
        # IMPORTANT:
        #
        # We do NOT require exactly one of each color here.
        #
        # This scanner only scans ONE face.
        #
        # A valid Rubik's Cube face can naturally contain
        # multiple stickers of the same color.
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

        if len(color_counts) > 1:

            dominant_color = max(
                color_counts,
                key=color_counts.get,
            )

            dominant_count = color_counts[
                dominant_color
            ]

            if dominant_count >= 8:

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
    ) -> float:

        """
        Combine geometric detection and color classification
        confidence.

        The sticker classifier receives slightly more weight
        because correct color recognition is critical for
        the later cube-state engine.
        """

        detection_confidence = max(
            0.0,
            min(
                1.0,
                detection_confidence,
            ),
        )

        sticker_confidence = max(
            0.0,
            min(
                1.0,
                sticker_confidence,
            ),
        )

        return float(
            (
                detection_confidence * 0.40
            )
            + (
                sticker_confidence * 0.60
            )
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

