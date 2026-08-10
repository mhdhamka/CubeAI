
"""
CubeAI Scanner

High-level pipeline that combines:

1. Cube detection
2. Face/sticker detection
3. Color classification

The scanner converts an image of a Rubik's Cube face into
a 3x3 color grid.
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
# Data structures
# ============================================================================

@dataclass
class StickerResult:
    row: int
    col: int
    color: str
    confidence: float
    bgr: tuple[int, int, int]


@dataclass
class ScanResult:
    success: bool
    colors: list[list[str]]
    stickers: list[StickerResult]
    confidence: float
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "colors": self.colors,
            "stickers": [
                asdict(sticker)
                for sticker in self.stickers
            ],
            "confidence": self.confidence,
            "error": self.error,
        }


# ============================================================================
# Scanner
# ============================================================================

class CubeScanner:
    """
    High-level Rubik's Cube face scanner.

    Pipeline:

        image
          ↓
        cube detector
          ↓
        perspective warp
          ↓
        face detector
          ↓
        9 sticker regions
          ↓
        color classifier
          ↓
        3x3 color matrix
    """

    def __init__(
        self,
        cube_detector: Any = None,
        face_detector: Any = None,
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

    # ========================================================================
    # Public API
    # ========================================================================

    def scan(
        self,
        image: np.ndarray,
    ) -> ScanResult:

        # --------------------------------------------------------------------
        # Validate input
        # --------------------------------------------------------------------

        if image is None:
            return ScanResult(
                success=False,
                colors=[],
                stickers=[],
                confidence=0.0,
                error="Input image is empty.",
            )

        if not isinstance(image, np.ndarray):
            return ScanResult(
                success=False,
                colors=[],
                stickers=[],
                confidence=0.0,
                error="Input must be an OpenCV image.",
            )

        if image.size == 0:
            return ScanResult(
                success=False,
                colors=[],
                stickers=[],
                confidence=0.0,
                error="Input image contains no pixels.",
            )

        try:

            # ================================================================
            # Step 1: Detect cube
            # ================================================================

            print("Step 1: Detecting cube...")

            cube_image = self._detect_cube(image)

            if cube_image is None:
                raise RuntimeError(
                    "Cube detector returned no image."
                )

            cube_height, cube_width = cube_image.shape[:2]

            print(
                f"  Cube image: "
                f"{cube_width}x{cube_height}"
            )

            # ================================================================
            # Step 2: Detect stickers
            # ================================================================

            print("Step 2: Detecting stickers...")

            regions = self._detect_face(
                cube_image
            )

            if regions is None:
                raise RuntimeError(
                    "Face detector returned no regions."
                )

            print(
                f"  Detected regions: {len(regions)}"
            )

            if len(regions) != 9:
                raise RuntimeError(
                    f"Expected 9 stickers, "
                    f"found {len(regions)}."
                )

            # ================================================================
            # Step 3: Classify colors
            # ================================================================

            print("Step 3: Classifying colors...")

            stickers: list[StickerResult] = []

            for index, region in enumerate(regions):

                row = index // 3
                col = index % 3

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
            # Step 4: Build 3x3 matrix
            # ================================================================

            colors = [
                [
                    stickers[row * 3 + col].color
                    for col in range(3)
                ]
                for row in range(3)
            ]

            confidence = self._average_confidence(
                stickers
            )

            return ScanResult(
                success=True,
                colors=colors,
                stickers=stickers,
                confidence=confidence,
            )

        except Exception as exc:

            return ScanResult(
                success=False,
                colors=[],
                stickers=[],
                confidence=0.0,
                error=str(exc),
            )

    # ========================================================================
    # Cube detection
    # ========================================================================

    def _detect_cube(
        self,
        image: np.ndarray,
    ) -> Optional[np.ndarray]:

        if self.cube_detector is None:

            if CUBE_DETECTOR_ERROR:
                raise RuntimeError(
                    "CubeDetector is unavailable: "
                    f"{CUBE_DETECTOR_ERROR}"
                )

            return image

        detector = self.cube_detector

        # --------------------------------------------------------------------
        # Call the actual CubeDetector.detect() API
        # --------------------------------------------------------------------

        if not hasattr(detector, "detect"):

            raise RuntimeError(
                "CubeDetector does not provide a detect() method."
            )

        try:

            result = detector.detect(image)

        except Exception as exc:

            raise RuntimeError(
                f"Cube detection failed: {exc}"
            ) from exc

        # --------------------------------------------------------------------
        # IMPORTANT:
        #
        # CubeDetector.detect() returns a CubeFace object.
        #
        # CubeFace contains:
        #
        #     result.warped
        #
        # which is the perspective-corrected 600x600 cube face.
        # --------------------------------------------------------------------

        if hasattr(result, "warped"):

            warped = result.warped

            if isinstance(warped, np.ndarray):

                if warped.size == 0:

                    raise RuntimeError(
                        "Cube detector returned an empty warped face."
                    )

                print(
                    "  Cube face detected!"
                )

                if hasattr(result, "confidence"):

                    print(
                        f"  Detection confidence: "
                        f"{float(result.confidence):.2f}"
                    )

                print(
                    f"  Using warped face: "
                    f"{warped.shape[1]}x{warped.shape[0]}"
                )

                return warped

        # --------------------------------------------------------------------
        # Direct NumPy result
        # --------------------------------------------------------------------

        if isinstance(result, np.ndarray):

            if result.size == 0:

                raise RuntimeError(
                    "Cube detector returned an empty image."
                )

            print(
                f"  Cube image: "
                f"{result.shape[1]}x{result.shape[0]}"
            )

            return result

        # --------------------------------------------------------------------
        # Dictionary result
        # --------------------------------------------------------------------

        if isinstance(result, dict):

            for key in (
                "warped",
                "warped_image",
                "image",
                "crop",
                "cropped",
                "cube",
                "roi",
            ):

                value = result.get(key)

                if isinstance(value, np.ndarray):

                    if value.size == 0:

                        continue

                    print(
                        f"  Using cube detector result: "
                        f"{key}"
                    )

                    print(
                        f"  Size: "
                        f"{value.shape[1]}x"
                        f"{value.shape[0]}"
                    )

                    return value

        # --------------------------------------------------------------------
        # Nothing usable returned
        # --------------------------------------------------------------------

        raise RuntimeError(
            "Cube detector did not return a usable "
            "warped cube face."
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

        # --------------------------------------------------------------------
        # Detect stickers
        # --------------------------------------------------------------------

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
            "Face detector returned an "
            "unsupported result."
        )

    # ========================================================================
    # Extract sticker BGR
    # ========================================================================

    def _extract_bgr(
        self,
        image: np.ndarray,
        region: Any,
    ) -> tuple[int, int, int]:

        # --------------------------------------------------------------------
        # Tuple/list: (x, y, w, h)
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

            # x, y, width, height
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

            # x, y, w, h
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

            # x1, y1, x2, y2
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

            # BGR already supplied
            if "bgr" in region:

                bgr = region["bgr"]

                return (
                    int(bgr[0]),
                    int(bgr[1]),
                    int(bgr[2]),
                )

            # Center supplied
            if "center" in region:

                center = region["center"]

                return self._sample_center(
                    image,
                    int(center[0]),
                    int(center[1]),
                )

        # --------------------------------------------------------------------
        # Object: x, y, width, height
        #
        # Matches your StickerRegion:
        #
        # StickerRegion(
        #     index=0,
        #     x=92,
        #     y=92,
        #     width=116,
        #     height=116,
        #     center_x=150,
        #     center_y=150
        # )
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
        # Object: center_x, center_y
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
        # Ignore approximately 20% around the border.
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

        mean = np.mean(
            roi.reshape(-1, 3),
            axis=0,
        )

        return (
            int(round(mean[0])),
            int(round(mean[1])),
            int(round(mean[2])),
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

        mean = np.mean(
            roi.reshape(-1, 3),
            axis=0,
        )

        return (
            int(round(mean[0])),
            int(round(mean[1])),
            int(round(mean[2])),
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
        # Your colorClassifier.py returns ColorResult
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
        # Tuple result
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
        # Dictionary result
        # --------------------------------------------------------------------

        if isinstance(
            result,
            dict,
        ):

            color = result.get(
                "color",
                result.get(
                    "label",
                    "unknown",
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


# ============================================================================
# Convenience function
# ============================================================================

def scan_image(
    image_path: str,
) -> ScanResult:

    image = cv2.imread(
        image_path,
        cv2.IMREAD_COLOR,
    )

    if image is None:

        return ScanResult(
            success=False,
            colors=[],
            stickers=[],
            confidence=0.0,
            error=(
                f"Could not load image: "
                f"{image_path}"
            ),
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

    print("CubeAI Scanner")
    print("--------------")

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "  py ai\\vision\\scanner.py "
            "<image>"
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

    if not result.success:

        print(
            "Scan failed:"
        )

        print(
            f"  {result.error}"
        )

        return

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
        f"Confidence: "
        f"{result.confidence:.2f}"
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


if __name__ == "__main__":
    main()

