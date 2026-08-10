"""
CubeAI Face Detector

Detects the 9 sticker regions on one Rubik's Cube face.

Pipeline:
    image
      -> grayscale
      -> blur
      -> edge detection
      -> contour detection
      -> square filtering
      -> candidate ranking
      -> 9 sticker regions
      -> row-major ordering

The detector returns the center coordinates and bounding boxes
for the 9 stickers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np


# ============================================================
# Data structures
# ============================================================

@dataclass
class StickerRegion:
    """
    A detected sticker region.
    """

    index: int
    x: int
    y: int
    width: int
    height: int
    center_x: int
    center_y: int

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return (
            self.x,
            self.y,
            self.width,
            self.height,
        )

    @property
    def center(self) -> Tuple[int, int]:
        return (
            self.center_x,
            self.center_y,
        )


# ============================================================
# Face detector
# ============================================================

class FaceDetector:
    """
    Detect the 9 stickers belonging to one visible cube face.
    """

    def __init__(
        self,
        min_area: int = 150,
        max_area_ratio: float = 0.20,
        min_aspect_ratio: float = 0.55,
        max_aspect_ratio: float = 1.80,
    ):
        self.min_area = min_area
        self.max_area_ratio = max_area_ratio
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def detect(
        self,
        image: np.ndarray,
    ) -> List[StickerRegion]:

        if image is None:
            raise ValueError(
                "FaceDetector.detect() received an empty image."
            )

        if image.size == 0:
            raise ValueError(
                "FaceDetector.detect() received an empty image."
            )

        if len(image.shape) != 3:
            raise ValueError(
                "FaceDetector.detect() expects a BGR image."
            )

        height, width = image.shape[:2]

        if height < 50 or width < 50:
            raise ValueError(
                "Image is too small for face detection."
            )

        # ----------------------------------------------------
        # Preprocessing
        # ----------------------------------------------------

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        # Slightly stronger blur helps remove small noise while
        # preserving sticker boundaries.
        blurred = cv2.GaussianBlur(
            gray,
            (5, 5),
            0,
        )

        # ----------------------------------------------------
        # Generate several edge maps.
        #
        # Different lighting conditions can make one threshold
        # miss some stickers, so we combine multiple approaches.
        # ----------------------------------------------------

        edge_maps = []

        for low, high in [
            (30, 100),
            (50, 150),
            (80, 180),
            (100, 200),
        ]:
            edges = cv2.Canny(
                blurred,
                low,
                high,
            )

            kernel = np.ones(
                (3, 3),
                np.uint8,
            )

            edges = cv2.morphologyEx(
                edges,
                cv2.MORPH_CLOSE,
                kernel,
                iterations=2,
            )

            edge_maps.append(edges)

        # ----------------------------------------------------
        # Collect candidates from all edge maps.
        # ----------------------------------------------------

        candidates = []

        for edges in edge_maps:

            contours, _ = cv2.findContours(
                edges,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            for contour in contours:

                candidate = self._contour_to_candidate(
                    contour,
                    width,
                    height,
                )

                if candidate is None:
                    continue

                candidates.append(candidate)

        # ----------------------------------------------------
        # Deduplicate overlapping candidates.
        # ----------------------------------------------------

        candidates = self._deduplicate(
            candidates
        )

        # ----------------------------------------------------
        # If normal contour detection doesn't find enough,
        # attempt a grid-based fallback.
        # ----------------------------------------------------

        if len(candidates) < 9:

            fallback = self._grid_candidates(
                image
            )

            candidates = self._merge_candidates(
                candidates,
                fallback,
            )

        # ----------------------------------------------------
        # Need at least 9.
        # ----------------------------------------------------

        if len(candidates) < 9:

            raise RuntimeError(
                "Could not detect 9 stickers. "
                f"Found {len(candidates)} candidates."
            )

        # ----------------------------------------------------
        # Select the best 9 candidates.
        # ----------------------------------------------------

        selected = self._select_best_n(
            candidates,
            9,
        )

        # ----------------------------------------------------
        # Order:
        #
        # 0 1 2
        # 3 4 5
        # 6 7 8
        # ----------------------------------------------------

        ordered = self._sort_grid(
            selected
        )

        # ----------------------------------------------------
        # Convert dictionaries to StickerRegion objects.
        # ----------------------------------------------------

        regions = []

        for index, candidate in enumerate(ordered):

            x = candidate["x"]
            y = candidate["y"]
            w = candidate["w"]
            h = candidate["h"]

            regions.append(
                StickerRegion(
                    index=index,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    center_x=x + w // 2,
                    center_y=y + h // 2,
                )
            )

        return regions

    # ========================================================
    # Candidate extraction
    # ========================================================

    def _contour_to_candidate(
        self,
        contour,
        image_width: int,
        image_height: int,
    ):

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        image_area = (
            image_width * image_height
        )

        # Minimum size.
        if area < self.min_area:
            return None

        # Maximum size.
        if area > image_area * self.max_area_ratio:
            return None

        if h == 0:
            return None

        aspect = w / h

        if (
            aspect < self.min_aspect_ratio
            or aspect > self.max_aspect_ratio
        ):
            return None

        contour_area = cv2.contourArea(
            contour
        )

        if contour_area <= 0:
            return None

        rectangularity = (
            contour_area / area
        )

        # Sticker contours don't necessarily form
        # perfect rectangles, so keep this relatively loose.
        if rectangularity < 0.35:
            return None

        perimeter = cv2.arcLength(
            contour,
            True,
        )

        if perimeter <= 0:
            return None

        approximation = cv2.approxPolyDP(
            contour,
            0.04 * perimeter,
            True,
        )

        # Prefer quadrilateral shapes but don't require them.
        shape_score = 1.0

        if len(approximation) == 4:
            shape_score = 1.25

        return {
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "area": area,
            "center_x": x + w / 2,
            "center_y": y + h / 2,
            "rectangularity": rectangularity,
            "shape_score": shape_score,
        }

    # ========================================================
    # Candidate deduplication
    # ========================================================

    def _deduplicate(
        self,
        candidates,
    ):

        if not candidates:
            return []

        # Larger / better candidates first.
        candidates = sorted(
            candidates,
            key=lambda c: (
                c["shape_score"],
                c["rectangularity"],
                c["area"],
            ),
            reverse=True,
        )

        kept = []

        for candidate in candidates:

            duplicate = False

            for existing in kept:

                if self._overlap(
                    candidate,
                    existing,
                ) > 0.45:

                    duplicate = True
                    break

            if not duplicate:
                kept.append(candidate)

        return kept

    def _overlap(
        self,
        a,
        b,
    ):

        ax1 = a["x"]
        ay1 = a["y"]
        ax2 = ax1 + a["w"]
        ay2 = ay1 + a["h"]

        bx1 = b["x"]
        by1 = b["y"]
        bx2 = bx1 + b["w"]
        by2 = by1 + b["h"]

        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0

        intersection = (
            (ix2 - ix1)
            * (iy2 - iy1)
        )

        area_a = a["w"] * a["h"]
        area_b = b["w"] * b["h"]

        smaller = min(
            area_a,
            area_b,
        )

        if smaller <= 0:
            return 0.0

        return intersection / smaller

    # ========================================================
    # Grid fallback
    # ========================================================

    def _grid_candidates(
        self,
        image: np.ndarray,
    ):

        height, width = image.shape[:2]

        candidates = []

        # We divide the image into a 3x3 grid and inspect
        # each cell for a likely sticker region.
        #
        # This is intentionally conservative: the grid fallback
        # only supplies candidates when contour detection misses
        # stickers.

        cell_width = width / 3
        cell_height = height / 3

        for row in range(3):

            for col in range(3):

                left = int(
                    col * cell_width
                )

                top = int(
                    row * cell_height
                )

                right = int(
                    (col + 1) * cell_width
                )

                bottom = int(
                    (row + 1) * cell_height
                )

                cell = image[
                    top:bottom,
                    left:right,
                ]

                if cell.size == 0:
                    continue

                gray = cv2.cvtColor(
                    cell,
                    cv2.COLOR_BGR2GRAY,
                )

                # Estimate a region around the center of the cell.
                ch, cw = gray.shape[:2]

                margin_x = int(
                    cw * 0.18
                )

                margin_y = int(
                    ch * 0.18
                )

                x = left + margin_x
                y = top + margin_y

                w = cw - (
                    margin_x * 2
                )

                h = ch - (
                    margin_y * 2
                )

                if w <= 0 or h <= 0:
                    continue

                candidates.append(
                    {
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h,
                        "area": w * h,
                        "center_x": x + w / 2,
                        "center_y": y + h / 2,
                        "rectangularity": 0.5,
                        "shape_score": 0.5,
                    }
                )

        return candidates

    # ========================================================
    # Merge candidates
    # ========================================================

    def _merge_candidates(
        self,
        existing,
        fallback,
    ):

        merged = list(existing)

        for candidate in fallback:

            duplicate = False

            for current in merged:

                if self._overlap(
                    candidate,
                    current,
                ) > 0.30:

                    duplicate = True
                    break

            if not duplicate:
                merged.append(candidate)

        return merged

    # ========================================================
    # Select best 9
    # ========================================================

    def _select_best_n(
        self,
        candidates,
        n: int,
    ):

        if len(candidates) <= n:
            return candidates

        # First determine approximate center of candidate cluster.
        center_x = np.mean(
            [
                c["center_x"]
                for c in candidates
            ]
        )

        center_y = np.mean(
            [
                c["center_y"]
                for c in candidates
            ]
        )

        def score(candidate):

            distance = np.sqrt(
                (
                    candidate["center_x"]
                    - center_x
                ) ** 2
                +
                (
                    candidate["center_y"]
                    - center_y
                ) ** 2
            )

            shape = candidate[
                "shape_score"
            ]

            rectangularity = candidate[
                "rectangularity"
            ]

            return (
                shape * 3.0
                + rectangularity * 2.0
                - distance * 0.001
            )

        return sorted(
            candidates,
            key=score,
            reverse=True,
        )[:n]

    # ========================================================
    # Sort into 3x3 layout
    # ========================================================

    def _sort_grid(
        self,
        candidates,
    ):

        candidates = list(candidates)

        if len(candidates) != 9:
            raise RuntimeError(
                "Internal detector error: "
                "expected exactly 9 candidates."
            )

        # Sort vertically first.
        candidates.sort(
            key=lambda c: c["center_y"]
        )

        rows = [
            candidates[0:3],
            candidates[3:6],
            candidates[6:9],
        ]

        # Sort each row horizontally.
        for row in rows:
            row.sort(
                key=lambda c: c["center_x"]
            )

        return [
            candidate
            for row in rows
            for candidate in row
        ]


# ============================================================
# Drawing helper
# ============================================================

def draw_regions(
    image: np.ndarray,
    regions: List[StickerRegion],
) -> np.ndarray:

    output = image.copy()

    for region in regions:

        cv2.rectangle(
            output,
            (
                region.x,
                region.y,
            ),
            (
                region.x
                + region.width,
                region.y
                + region.height,
            ),
            (0, 255, 0),
            2,
        )

        cv2.putText(
            output,
            str(region.index),
            (
                region.center_x - 8,
                region.center_y + 8,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    return output


# ============================================================
# Standalone test
# ============================================================

if __name__ == "__main__":

    print("CubeAI Face Detector")
    print("--------------------")

    # --------------------------------------------------------
    # Create a synthetic 3x3 cube face for testing.
    #
    # This means the detector can be tested without requiring
    # a real camera/image file.
    # --------------------------------------------------------

    test_image = np.zeros(
        (600, 600, 3),
        dtype=np.uint8,
    )

    sticker_size = 120
    gap = 15

    start_x = 90
    start_y = 90

    for row in range(3):

        for col in range(3):

            x = (
                start_x
                + col
                * (
                    sticker_size
                    + gap
                )
            )

            y = (
                start_y
                + row
                * (
                    sticker_size
                    + gap
                )
            )

            cv2.rectangle(
                test_image,
                (x, y),
                (
                    x + sticker_size,
                    y + sticker_size,
                ),
                (255, 255, 255),
                -1,
            )

            cv2.rectangle(
                test_image,
                (x, y),
                (
                    x + sticker_size,
                    y + sticker_size,
                ),
                (0, 0, 0),
                3,
            )

    detector = FaceDetector()

    try:

        regions = detector.detect(
            test_image
        )

        print(
            f"Detected {len(regions)} stickers."
        )

        for region in regions:

            print(
                f"  [{region.index}] "
                f"bbox={region.bbox} "
                f"center={region.center}"
            )

        debug = draw_regions(
            test_image,
            regions,
        )

        output_path = (
            "face_detector_debug.png"
        )

        cv2.imwrite(
            output_path,
            debug,
        )

        print(
            f"\nDebug image written to "
            f"{output_path}"
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

        raise