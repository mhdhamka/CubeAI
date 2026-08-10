"""
CubeAI Cube Detector

Detects the visible Rubik's Cube face from an image.

Detection strategy:

1. Edge / contour based quadrilateral detection
2. Candidate validation
3. Prefer the large outer 3x3 cube face
4. Sticker-grid fallback
5. Perspective correction

The detector returns a normalized 600x600 cube face.

Sticker detection is handled separately by faceDetector.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import sys

import cv2
import numpy as np


# ============================================================
# Data structures
# ============================================================

@dataclass
class CubeFace:
    """
    Represents the detected visible face of a Rubik's Cube.
    """

    corners: np.ndarray
    width: int
    height: int
    confidence: float
    warped: Optional[np.ndarray] = None

    @property
    def top_left(self) -> Tuple[int, int]:
        return tuple(self.corners[0].astype(int))

    @property
    def top_right(self) -> Tuple[int, int]:
        return tuple(self.corners[1].astype(int))

    @property
    def bottom_right(self) -> Tuple[int, int]:
        return tuple(self.corners[2].astype(int))

    @property
    def bottom_left(self) -> Tuple[int, int]:
        return tuple(self.corners[3].astype(int))


# ============================================================
# Cube detector
# ============================================================

class CubeDetector:

    def __init__(
        self,
        output_size: int = 600,
        min_area_ratio: float = 0.04,
        max_area_ratio: float = 0.90,
        min_face_size: int = 250,
    ):

        self.output_size = output_size
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio
        self.min_face_size = min_face_size

    # ========================================================
    # Public API
    # ========================================================

    def detect(
        self,
        image: np.ndarray,
    ) -> CubeFace:

        if image is None:
            raise ValueError(
                "CubeDetector.detect() received an empty image."
            )

        if image.size == 0:
            raise ValueError(
                "CubeDetector.detect() received an empty image."
            )

        if len(image.shape) != 3:
            raise ValueError(
                "CubeDetector.detect() expects a BGR image."
            )

        height, width = image.shape[:2]

        if height < 100 or width < 100:
            raise ValueError(
                "Image is too small for cube detection."
            )

        print(
            f"  Input image: {width}x{height}"
        )

        # ====================================================
        # Strategy 1:
        # Quadrilateral detection
        # ====================================================

        candidates = self._find_quadrilateral_candidates(
            image
        )

        print(
            f"  Quadrilateral candidates: "
            f"{len(candidates)}"
        )

        candidates = self._deduplicate(
            candidates
        )

        print(
            f"  Candidates after filtering: "
            f"{len(candidates)}"
        )

        # ----------------------------------------------------
        # Candidate debugging
        # ----------------------------------------------------

        if candidates:

            print(
                "  Candidate sizes:"
            )

            debug_candidates = sorted(
                candidates,
                key=lambda c: c["score"],
                reverse=True,
            )

            for index, candidate in enumerate(
                debug_candidates[:10]
            ):

                corners = candidate["corners"]

                x_min = float(
                    np.min(corners[:, 0])
                )

                x_max = float(
                    np.max(corners[:, 0])
                )

                y_min = float(
                    np.min(corners[:, 1])
                )

                y_max = float(
                    np.max(corners[:, 1])
                )

                candidate_width = (
                    x_max - x_min
                )

                candidate_height = (
                    y_max - y_min
                )

                print(
                    f"    [{index}] "
                    f"{candidate_width:.0f}x"
                    f"{candidate_height:.0f} "
                    f"area={candidate['area_ratio']:.3f} "
                    f"score={candidate['score']:.3f}"
                )

        # ====================================================
        # Select best quadrilateral
        # ====================================================

        if candidates:

            best = max(
                candidates,
                key=lambda c: c["score"],
            )

            corners = self._order_corners(
                best["corners"]
            )

            print(
                "  Selected cube candidate:"
            )

            print(
                f"    Width: "
                f"{best['width']:.0f}px"
            )

            print(
                f"    Height: "
                f"{best['height']:.0f}px"
            )

            print(
                f"    Area ratio: "
                f"{best['area_ratio']:.3f}"
            )

            print(
                f"    Score: "
                f"{best['score']:.3f}"
            )

            warped = self._warp_face(
                image,
                corners,
            )

            confidence = float(
                min(
                    max(
                        best["score"],
                        0.0,
                    ),
                    1.0,
                )
            )

            return CubeFace(
                corners=corners,
                width=self.output_size,
                height=self.output_size,
                confidence=confidence,
                warped=warped,
            )

        # ====================================================
        # Strategy 2:
        # Sticker grid detection
        # ====================================================

        print(
            "  Quadrilateral detection failed."
        )

        print(
            "  Trying sticker-grid detection..."
        )

        grid_result = self._detect_sticker_grid(
            image
        )

        if grid_result is None:

            raise RuntimeError(
                "Could not detect a cube face."
            )

        grid_corners, grid_confidence = (
            grid_result
        )

        print(
            "  Sticker grid detected!"
        )

        corners = self._order_corners(
            grid_corners
        )

        warped = self._warp_face(
            image,
            corners,
        )

        return CubeFace(
            corners=corners,
            width=self.output_size,
            height=self.output_size,
            confidence=grid_confidence,
            warped=warped,
        )

    # ========================================================
    # Strategy 1
    # ========================================================

    def _find_quadrilateral_candidates(
        self,
        image: np.ndarray,
    ):

        height, width = image.shape[:2]

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        blurred = cv2.GaussianBlur(
            gray,
            (5, 5),
            0,
        )

        edge_maps = []

        thresholds = [
            (15, 60),
            (20, 80),
            (30, 100),
            (40, 120),
            (50, 150),
            (70, 180),
            (90, 200),
        ]

        for low, high in thresholds:

            edges = cv2.Canny(
                blurred,
                low,
                high,
            )

            kernel = np.ones(
                (7, 7),
                np.uint8,
            )

            edges = cv2.morphologyEx(
                edges,
                cv2.MORPH_CLOSE,
                kernel,
                iterations=2,
            )

            edge_maps.append(
                edges
            )

        candidates = []

        for edges in edge_maps:

            contours, _ = cv2.findContours(
                edges,
                cv2.RETR_LIST,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            for contour in contours:

                candidate = (
                    self._contour_to_candidate(
                        contour,
                        width,
                        height,
                    )
                )

                if candidate is not None:
                    candidates.append(
                        candidate
                    )

        return candidates

    # ========================================================
    # Candidate extraction
    # ========================================================

    def _contour_to_candidate(
        self,
        contour,
        image_width: int,
        image_height: int,
    ):

        image_area = (
            image_width
            * image_height
        )

        contour_area = cv2.contourArea(
            contour
        )

        if contour_area <= 0:
            return None

        area_ratio = (
            contour_area
            / image_area
        )

        if area_ratio < self.min_area_ratio:
            return None

        if area_ratio > self.max_area_ratio:
            return None

        perimeter = cv2.arcLength(
            contour,
            True,
        )

        if perimeter <= 0:
            return None

        approximation = cv2.approxPolyDP(
            contour,
            0.02 * perimeter,
            True,
        )

        if len(approximation) != 4:
            return None

        corners = (
            approximation
            .reshape(4, 2)
            .astype(np.float32)
        )

        if not cv2.isContourConvex(
            approximation
        ):
            return None

        # ----------------------------------------------------
        # Bounding box
        # ----------------------------------------------------

        x, y, w, h = cv2.boundingRect(
            approximation
        )

        if w <= 0 or h <= 0:
            return None

        # Reject individual stickers.
        if (
            w < self.min_face_size
            or h < self.min_face_size
        ):
            return None

        # ----------------------------------------------------
        # Aspect ratio
        # ----------------------------------------------------

        aspect_ratio = (
            w / h
        )

        if (
            aspect_ratio < 0.55
            or aspect_ratio > 1.80
        ):
            return None

        # ----------------------------------------------------
        # Side lengths
        # ----------------------------------------------------

        side_lengths = []

        for i in range(4):

            p1 = corners[i]

            p2 = corners[
                (i + 1) % 4
            ]

            distance = np.linalg.norm(
                p2 - p1
            )

            side_lengths.append(
                distance
            )

        if min(side_lengths) <= 0:
            return None

        max_side = max(
            side_lengths
        )

        min_side = min(
            side_lengths
        )

        side_ratio = (
            min_side
            / max_side
        )

        if side_ratio < 0.45:
            return None

        # ----------------------------------------------------
        # Border rejection
        # ----------------------------------------------------

        xs = corners[:, 0]
        ys = corners[:, 1]

        touches_left = (
            np.min(xs) <= 1
        )

        touches_top = (
            np.min(ys) <= 1
        )

        touches_right = (
            np.max(xs)
            >= image_width - 2
        )

        touches_bottom = (
            np.max(ys)
            >= image_height - 2
        )

        touches_all_borders = (
            touches_left
            and touches_top
            and touches_right
            and touches_bottom
        )

        if touches_all_borders:
            return None

        # ----------------------------------------------------
        # Rectangularity
        # ----------------------------------------------------

        bounding_area = (
            w * h
        )

        rectangularity = (
            contour_area
            / bounding_area
        )

        if rectangularity < 0.45:
            return None

        # ----------------------------------------------------
        # Perspective consistency
        # ----------------------------------------------------

        top = np.linalg.norm(
            corners[1]
            - corners[0]
        )

        bottom = np.linalg.norm(
            corners[2]
            - corners[3]
        )

        left = np.linalg.norm(
            corners[3]
            - corners[0]
        )

        right = np.linalg.norm(
            corners[2]
            - corners[1]
        )

        horizontal_ratio = (
            min(top, bottom)
            / max(top, bottom)
        )

        vertical_ratio = (
            min(left, right)
            / max(left, right)
        )

        perspective_score = (
            horizontal_ratio
            + vertical_ratio
        ) / 2.0

        # ----------------------------------------------------
        # Square score
        # ----------------------------------------------------

        aspect_score = 1.0 - min(
            abs(
                np.log(
                    aspect_ratio
                )
            ),
            1.0,
        )

        # ----------------------------------------------------
        # Area score
        # ----------------------------------------------------

        area_score = min(
            area_ratio / 0.25,
            1.0,
        )

        # ----------------------------------------------------
        # Size score
        # ----------------------------------------------------

        size_score = min(
            min(w, h) / 600.0,
            1.0,
        )

        # ----------------------------------------------------
        # Center score
        # ----------------------------------------------------

        center_x = (
            x + w / 2.0
        )

        center_y = (
            y + h / 2.0
        )

        image_center_x = (
            image_width / 2.0
        )

        image_center_y = (
            image_height / 2.0
        )

        dx = (
            center_x
            - image_center_x
        ) / image_width

        dy = (
            center_y
            - image_center_y
        ) / image_height

        distance_from_center = np.sqrt(
            dx * dx
            + dy * dy
        )

        center_score = max(
            0.0,
            1.0
            - distance_from_center * 2.0,
        )

        # ----------------------------------------------------
        # Final score
        # ----------------------------------------------------

        score = (
            area_score * 0.30
            + size_score * 0.20
            + rectangularity * 0.15
            + side_ratio * 0.10
            + aspect_score * 0.10
            + perspective_score * 0.10
            + center_score * 0.05
        )

        return {
            "corners": corners,
            "score": score,
            "area": contour_area,
            "area_ratio": area_ratio,
            "width": float(w),
            "height": float(h),
        }

    # ========================================================
    # Strategy 2: Sticker grid detection
    #
    # This fallback is designed specifically for cases where
    # the cube's outer border is not detectable.
    #
    # Instead of trying to guess the grid from percentiles,
    # we explicitly build 3 X positions and 3 Y positions.
    # ========================================================

    def _detect_sticker_grid(
        self,
        image: np.ndarray,
    ) -> Optional[
        Tuple[np.ndarray, float]
    ]:

        height, width = image.shape[:2]

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        blurred = cv2.GaussianBlur(
            gray,
            (5, 5),
            0,
        )

        all_candidates = []

        # ----------------------------------------------------
        # Multiple edge maps
        # ----------------------------------------------------

        for low, high in [
            (15, 60),
            (25, 90),
            (40, 120),
            (60, 160),
            (80, 200),
        ]:

            edges = cv2.Canny(
                blurred,
                low,
                high,
            )

            kernel = np.ones(
                (5, 5),
                np.uint8,
            )

            edges = cv2.morphologyEx(
                edges,
                cv2.MORPH_CLOSE,
                kernel,
                iterations=2,
            )

            contours, _ = cv2.findContours(
                edges,
                cv2.RETR_LIST,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            image_area = (
                width * height
            )

            for contour in contours:

                area = cv2.contourArea(
                    contour
                )

                if area <= 0:
                    continue

                ratio = (
                    area
                    / image_area
                )

                # Sticker regions.
                if ratio < 0.002:
                    continue

                if ratio > 0.15:
                    continue

                perimeter = cv2.arcLength(
                    contour,
                    True,
                )

                if perimeter <= 0:
                    continue

                approx = cv2.approxPolyDP(
                    contour,
                    0.035 * perimeter,
                    True,
                )

                if len(approx) != 4:
                    continue

                if not cv2.isContourConvex(
                    approx
                ):
                    continue

                x, y, w, h = cv2.boundingRect(
                    approx
                )

                if (
                    w < 30
                    or h < 30
                ):
                    continue

                aspect = (
                    w / h
                )

                if (
                    aspect < 0.60
                    or aspect > 1.67
                ):
                    continue

                rectangularity = (
                    area
                    / (w * h)
                )

                if rectangularity < 0.45:
                    continue

                center_x = (
                    x + w / 2.0
                )

                center_y = (
                    y + h / 2.0
                )

                all_candidates.append(
                    {
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h,
                        "cx": center_x,
                        "cy": center_y,
                        "area": area,
                    }
                )

        # ----------------------------------------------------
        # Remove duplicates from multiple edge maps.
        # ----------------------------------------------------

        sticker_candidates = (
            self._deduplicate_stickers(
                all_candidates
            )
        )

        print(
            f"  Sticker candidates: "
            f"{len(sticker_candidates)}"
        )

        if len(sticker_candidates) < 5:
            return None

        # ----------------------------------------------------
        # Keep reasonable candidates.
        #
        # The largest 9-20 candidates are much more useful
        # than dozens of weak background contours.
        # ----------------------------------------------------

        sticker_candidates = sorted(
            sticker_candidates,
            key=lambda item: item["area"],
            reverse=True,
        )

        sticker_candidates = (
            sticker_candidates[:25]
        )

        # ----------------------------------------------------
        # Find the best 3x3 arrangement.
        # ----------------------------------------------------

        best = self._find_best_3x3_grid(
            sticker_candidates
        )

        if best is None:
            return None

        grid_points, grid_score = best

        # ----------------------------------------------------
        # grid_points contains 9 centers:
        #
        # 0 1 2
        # 3 4 5
        # 6 7 8
        # ----------------------------------------------------

        xs = grid_points[:, 0].reshape(
            3,
            3,
        )

        ys = grid_points[:, 1].reshape(
            3,
            3,
        )

        # ----------------------------------------------------
        # Average center positions for each row/column.
        # This makes the estimate more stable when the cube
        # is slightly perspective distorted.
        # ----------------------------------------------------

        column_x = np.mean(
            xs,
            axis=0,
        )

        row_y = np.mean(
            ys,
            axis=1,
        )

        # ----------------------------------------------------
        # Estimate sticker spacing.
        # ----------------------------------------------------

        spacing_x = (
            (
                column_x[1]
                - column_x[0]
            )
            + (
                column_x[2]
                - column_x[1]
            )
        ) / 2.0

        spacing_y = (
            (
                row_y[1]
                - row_y[0]
            )
            + (
                row_y[2]
                - row_y[1]
            )
        ) / 2.0

        if (
            spacing_x <= 20
            or spacing_y <= 20
        ):
            return None

        # ----------------------------------------------------
        # Estimate sticker dimensions.
        # ----------------------------------------------------

        sticker_widths = []
        sticker_heights = []

        for candidate in sticker_candidates:

            sticker_widths.append(
                candidate["w"]
            )

            sticker_heights.append(
                candidate["h"]
            )

        median_sticker_width = float(
            np.median(
                sticker_widths
            )
        )

        median_sticker_height = float(
            np.median(
                sticker_heights
            )
        )

        # ----------------------------------------------------
        # Important:
        #
        # The outer cube boundary is approximately half a
        # sticker-spacing outside the outer sticker centers.
        #
        # We use the measured sticker size as a secondary
        # estimate to make this robust.
        # ----------------------------------------------------

        half_cell_x = max(
            spacing_x * 0.50,
            median_sticker_width * 0.50,
        )

        half_cell_y = max(
            spacing_y * 0.50,
            median_sticker_height * 0.50,
        )

        cube_left = (
            column_x[0]
            - half_cell_x
        )

        cube_right = (
            column_x[2]
            + half_cell_x
        )

        cube_top = (
            row_y[0]
            - half_cell_y
        )

        cube_bottom = (
            row_y[2]
            + half_cell_y
        )

        # ----------------------------------------------------
        # Clamp to image.
        # ----------------------------------------------------

        cube_left = max(
            0.0,
            cube_left,
        )

        cube_top = max(
            0.0,
            cube_top,
        )

        cube_right = min(
            float(width - 1),
            cube_right,
        )

        cube_bottom = min(
            float(height - 1),
            cube_bottom,
        )

        cube_width = (
            cube_right
            - cube_left
        )

        cube_height = (
            cube_bottom
            - cube_top
        )

        if (
            cube_width < 250
            or cube_height < 250
        ):
            return None

        # ----------------------------------------------------
        # Cube face should be approximately square.
        # ----------------------------------------------------

        cube_aspect = (
            cube_width
            / cube_height
        )

        if (
            cube_aspect < 0.65
            or cube_aspect > 1.55
        ):
            return None

        # ----------------------------------------------------
        # Reject if the estimated face is basically the
        # entire image.
        # ----------------------------------------------------

        image_area = (
            width * height
        )

        cube_area_ratio = (
            cube_width
            * cube_height
            / image_area
        )

        if cube_area_ratio > 0.90:
            return None

        # ----------------------------------------------------
        # Print useful debugging information.
        # ----------------------------------------------------

        print(
            f"  Grid spacing: "
            f"{spacing_x:.1f} x "
            f"{spacing_y:.1f}"
        )

        print(
            f"  Estimated cube size: "
            f"{cube_width:.0f}x"
            f"{cube_height:.0f}"
        )

        print(
            f"  Grid score: "
            f"{grid_score:.3f}"
        )

        # ----------------------------------------------------
        # Return face corners.
        # ----------------------------------------------------

        corners = np.array(
            [
                [
                    cube_left,
                    cube_top,
                ],
                [
                    cube_right,
                    cube_top,
                ],
                [
                    cube_right,
                    cube_bottom,
                ],
                [
                    cube_left,
                    cube_bottom,
                ],
            ],
            dtype=np.float32,
        )

        # ----------------------------------------------------
        # Convert grid score into confidence.
        # ----------------------------------------------------

        confidence = float(
            min(
                0.95,
                max(
                    0.70,
                    0.70
                    + grid_score * 0.25,
                ),
            )
        )

        return (
            corners,
            confidence,
        )

    # ========================================================
    # Find best 3x3 grid
    # ========================================================

    def _find_best_3x3_grid(
        self,
        candidates,
    ):

        if len(candidates) < 5:
            return None

        # ----------------------------------------------------
        # Candidate center coordinates.
        # ----------------------------------------------------

        points = np.array(
            [
                [
                    candidate["cx"],
                    candidate["cy"],
                ]
                for candidate in candidates
            ],
            dtype=np.float32,
        )

        if len(points) < 5:
            return None

        best_grid = None
        best_score = -1.0

        # ----------------------------------------------------
        # We try each candidate as a possible center sticker.
        #
        # This works well because a Rubik's Cube face has a
        # very strong regular 3x3 geometric pattern.
        # ----------------------------------------------------

        for center_index, center in enumerate(
            points
        ):

            cx = float(center[0])
            cy = float(center[1])

            # ------------------------------------------------
            # Estimate nearest-neighbor distances.
            # ------------------------------------------------

            distances = []

            for index, point in enumerate(
                points
            ):

                if index == center_index:
                    continue

                distance = float(
                    np.linalg.norm(
                        point - center
                    )
                )

                distances.append(
                    distance
                )

            if len(distances) < 4:
                continue

            distances.sort()

            # The closest neighbors to the center should
            # normally be adjacent stickers.
            spacing_guess = float(
                np.median(
                    distances[:4]
                )
            )

            if spacing_guess < 30:
                continue

            # ------------------------------------------------
            # Build expected 3x3 positions.
            # ------------------------------------------------

            expected = []

            for row in range(3):

                for col in range(3):

                    expected_x = (
                        cx
                        + (
                            col - 1
                        )
                        * spacing_guess
                    )

                    expected_y = (
                        cy
                        + (
                            row - 1
                        )
                        * spacing_guess
                    )

                    expected.append(
                        [
                            expected_x,
                            expected_y,
                        ]
                    )

            expected = np.array(
                expected,
                dtype=np.float32,
            )

            matched = []

            used = set()

            total_error = 0.0

            valid = True

            # ------------------------------------------------
            # Match every expected grid position to the
            # nearest real sticker.
            # ------------------------------------------------

            for expected_point in expected:

                best_index = None
                best_distance = float(
                    "inf"
                )

                for index, point in enumerate(
                    points
                ):

                    if index in used:
                        continue

                    distance = float(
                        np.linalg.norm(
                            point
                            - expected_point
                        )
                    )

                    if distance < best_distance:

                        best_distance = (
                            distance
                        )

                        best_index = index

                # Allow fairly generous perspective / camera
                # error.
                tolerance = max(
                    spacing_guess * 0.40,
                    45.0,
                )

                if (
                    best_index is None
                    or best_distance > tolerance
                ):

                    valid = False
                    break

                used.add(
                    best_index
                )

                matched.append(
                    points[best_index]
                )

                total_error += (
                    best_distance
                )

            if not valid:
                continue

            # ------------------------------------------------
            # We need all 9 stickers for a reliable cube
            # face estimate.
            # ----------------------------------------------------

            if len(matched) != 9:
                continue

            matched = np.array(
                matched,
                dtype=np.float32,
            )

            average_error = (
                total_error / 9.0
            )

            error_score = max(
                0.0,
                1.0
                - (
                    average_error
                    / max(
                        spacing_guess,
                        1.0,
                    )
                ),
            )

            # ------------------------------------------------
            # Check that the grid covers a reasonable area.
            # ------------------------------------------------

            min_x = float(
                np.min(
                    matched[:, 0]
                )
            )

            max_x = float(
                np.max(
                    matched[:, 0]
                )
            )

            min_y = float(
                np.min(
                    matched[:, 1]
                )
            )

            max_y = float(
                np.max(
                    matched[:, 1]
                )
            )

            span_x = (
                max_x - min_x
            )

            span_y = (
                max_y - min_y
            )

            if (
                span_x < spacing_guess * 1.3
                or span_y < spacing_guess * 1.3
            ):
                continue

            span_ratio = (
                min(
                    span_x,
                    span_y,
                )
                / max(
                    span_x,
                    span_y,
                )
            )

            if span_ratio < 0.60:
                continue

            # ------------------------------------------------
            # Prefer larger and more regular grids.
            # ------------------------------------------------

            size_score = min(
                (
                    span_x
                    + span_y
                )
                / 1200.0,
                1.0,
            )

            grid_score = (
                error_score * 0.70
                + span_ratio * 0.15
                + size_score * 0.15
            )

            if grid_score > best_score:

                best_score = (
                    grid_score
                )

                # ------------------------------------------------
                # Reorder matched points into actual row/column
                # order instead of relying on matching order.
                # ------------------------------------------------

                ordered_grid = (
                    self._order_grid_points(
                        matched
                    )
                )

                best_grid = (
                    ordered_grid,
                    grid_score,
                )

        return best_grid

    # ========================================================
    # Order 9 sticker centers into:
    #
    # 0 1 2
    # 3 4 5
    # 6 7 8
    # ========================================================

    def _order_grid_points(
        self,
        points: np.ndarray,
    ) -> np.ndarray:

        points = np.asarray(
            points,
            dtype=np.float32,
        )

        # Sort by Y first.
        sorted_by_y = points[
            np.argsort(
                points[:, 1]
            )
        ]

        rows = [
            sorted_by_y[0:3],
            sorted_by_y[3:6],
            sorted_by_y[6:9],
        ]

        ordered = []

        for row in rows:

            row = row[
                np.argsort(
                    row[:, 0]
                )
            ]

            ordered.extend(
                row.tolist()
            )

        return np.array(
            ordered,
            dtype=np.float32,
        )

    # ========================================================
    # Sticker deduplication
    # ========================================================

    def _deduplicate_stickers(
        self,
        candidates,
    ):

        if not candidates:
            return []

        candidates = sorted(
            candidates,
            key=lambda item: item["area"],
            reverse=True,
        )

        kept = []

        for candidate in candidates:

            duplicate = False

            for existing in kept:

                dx = (
                    candidate["cx"]
                    - existing["cx"]
                )

                dy = (
                    candidate["cy"]
                    - existing["cy"]
                )

                distance = np.sqrt(
                    dx * dx
                    + dy * dy
                )

                average_size = (
                    (
                        candidate["w"]
                        + candidate["h"]
                        + existing["w"]
                        + existing["h"]
                    )
                    / 4.0
                )

                if distance < (
                    average_size * 0.50
                ):

                    duplicate = True
                    break

            if not duplicate:
                kept.append(
                    candidate
                )

        return kept

    # ========================================================
    # Deduplicate quadrilateral candidates
    # ========================================================

    def _deduplicate(
        self,
        candidates,
    ):

        if not candidates:
            return []

        candidates = sorted(
            candidates,
            key=lambda c: c["score"],
            reverse=True,
        )

        kept = []

        for candidate in candidates:

            duplicate = False

            for existing in kept:

                if self._candidate_overlap(
                    candidate,
                    existing,
                ) > 0.60:

                    duplicate = True
                    break

            if not duplicate:
                kept.append(
                    candidate
                )

        return kept

    # ========================================================
    # Candidate overlap
    # ========================================================

    def _candidate_overlap(
        self,
        a,
        b,
    ):

        ax1 = np.min(
            a["corners"][:, 0]
        )

        ay1 = np.min(
            a["corners"][:, 1]
        )

        ax2 = np.max(
            a["corners"][:, 0]
        )

        ay2 = np.max(
            a["corners"][:, 1]
        )

        bx1 = np.min(
            b["corners"][:, 0]
        )

        by1 = np.min(
            b["corners"][:, 1]
        )

        bx2 = np.max(
            b["corners"][:, 0]
        )

        by2 = np.max(
            b["corners"][:, 1]
        )

        ix1 = max(
            ax1,
            bx1,
        )

        iy1 = max(
            ay1,
            by1,
        )

        ix2 = min(
            ax2,
            bx2,
        )

        iy2 = min(
            ay2,
            by2,
        )

        if (
            ix2 <= ix1
            or iy2 <= iy1
        ):
            return 0.0

        intersection = (
            ix2 - ix1
        ) * (
            iy2 - iy1
        )

        area_a = (
            ax2 - ax1
        ) * (
            ay2 - ay1
        )

        area_b = (
            bx2 - bx1
        ) * (
            by2 - by1
        )

        smaller = min(
            area_a,
            area_b,
        )

        if smaller <= 0:
            return 0.0

        return (
            intersection
            / smaller
        )

    # ========================================================
    # Corner ordering
    # ========================================================

    def _order_corners(
        self,
        corners: np.ndarray,
    ) -> np.ndarray:

        ordered = np.zeros(
            (4, 2),
            dtype=np.float32,
        )

        sums = (
            corners[:, 0]
            + corners[:, 1]
        )

        differences = (
            corners[:, 0]
            - corners[:, 1]
        )

        # Top-left
        ordered[0] = corners[
            np.argmin(sums)
        ]

        # Top-right
        ordered[1] = corners[
            np.argmax(differences)
        ]

        # Bottom-right
        ordered[2] = corners[
            np.argmax(sums)
        ]

        # Bottom-left
        ordered[3] = corners[
            np.argmin(differences)
        ]

        return ordered

    # ========================================================
    # Perspective correction
    # ========================================================

    def _warp_face(
        self,
        image: np.ndarray,
        corners: np.ndarray,
    ) -> np.ndarray:

        destination = np.array(
            [
                [0, 0],
                [
                    self.output_size - 1,
                    0,
                ],
                [
                    self.output_size - 1,
                    self.output_size - 1,
                ],
                [
                    0,
                    self.output_size - 1,
                ],
            ],
            dtype=np.float32,
        )

        matrix = cv2.getPerspectiveTransform(
            corners,
            destination,
        )

        warped = cv2.warpPerspective(
            image,
            matrix,
            (
                self.output_size,
                self.output_size,
            ),
        )

        return warped


# ============================================================
# Debug drawing
# ============================================================

def draw_cube_face(
    image: np.ndarray,
    cube_face: CubeFace,
) -> np.ndarray:

    output = image.copy()

    points = (
        cube_face.corners
        .astype(np.int32)
    )

    cv2.polylines(
        output,
        [points],
        True,
        (0, 255, 0),
        4,
    )

    for index, point in enumerate(
        points
    ):

        x, y = point

        cv2.circle(
            output,
            (x, y),
            8,
            (0, 0, 255),
            -1,
        )

        cv2.putText(
            output,
            str(index),
            (
                x + 10,
                y - 10,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    cv2.putText(
        output,
        (
            f"Confidence: "
            f"{cube_face.confidence:.2f}"
        ),
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )

    return output


# ============================================================
# Synthetic test image
# ============================================================

def create_test_cube_image() -> np.ndarray:

    image = np.zeros(
        (700, 700, 3),
        dtype=np.uint8,
    )

    image[:] = (
        40,
        40,
        40,
    )

    points = np.array(
        [
            [130, 120],
            [560, 100],
            [590, 560],
            [110, 580],
        ],
        dtype=np.int32,
    )

    cv2.fillConvexPoly(
        image,
        points,
        (220, 220, 220),
    )

    cv2.polylines(
        image,
        [points],
        True,
        (20, 20, 20),
        8,
    )

    inner = np.array(
        [
            [145, 135],
            [545, 120],
            [570, 540],
            [130, 555],
        ],
        dtype=np.float32,
    )

    for row in range(1, 3):

        alpha = row / 3.0

        left = (
            inner[0] * (1 - alpha)
            + inner[3] * alpha
        )

        right = (
            inner[1] * (1 - alpha)
            + inner[2] * alpha
        )

        cv2.line(
            image,
            left.astype(np.int32),
            right.astype(np.int32),
            (20, 20, 20),
            5,
        )

    for col in range(1, 3):

        alpha = col / 3.0

        top = (
            inner[0] * (1 - alpha)
            + inner[1] * alpha
        )

        bottom = (
            inner[3] * (1 - alpha)
            + inner[2] * alpha
        )

        cv2.line(
            image,
            top.astype(np.int32),
            bottom.astype(np.int32),
            (20, 20, 20),
            5,
        )

    return image


# ============================================================
# Main
# ============================================================

def main() -> None:

    print(
        "CubeAI Cube Detector"
    )

    print(
        "--------------------"
    )

    if len(sys.argv) >= 2:

        image_path = sys.argv[1]

        print(
            f"Image: {image_path}"
        )

        image = cv2.imread(
            image_path,
            cv2.IMREAD_COLOR,
        )

        if image is None:

            print(
                f"ERROR: Could not load image: "
                f"{image_path}"
            )

            return

    else:

        print(
            "No image supplied."
        )

        print(
            "Using synthetic test image."
        )

        image = create_test_cube_image()

    print()

    detector = CubeDetector()

    try:

        cube_face = detector.detect(
            image
        )

        print(
            "\nCube face detected!"
        )

        print(
            f"Confidence: "
            f"{cube_face.confidence:.2f}"
        )

        print(
            "Corners:"
        )

        for index, corner in enumerate(
            cube_face.corners
        ):

            print(
                f"  {index}: "
                f"({corner[0]:.1f}, "
                f"{corner[1]:.1f})"
            )

        print(
            f"Warped size: "
            f"{cube_face.width}x"
            f"{cube_face.height}"
        )

        # ----------------------------------------------------
        # Debug image
        # ----------------------------------------------------

        debug = draw_cube_face(
            image,
            cube_face,
        )

        output_path = (
            "cube_detector_debug.png"
        )

        cv2.imwrite(
            output_path,
            debug,
        )

        print(
            f"\nDebug image written to "
            f"{output_path}"
        )

        # ----------------------------------------------------
        # Warped face
        # ----------------------------------------------------

        warped_path = (
            "cube_face_warped.png"
        )

        cv2.imwrite(
            warped_path,
            cube_face.warped,
        )

        print(
            f"Warped face written to "
            f"{warped_path}"
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

        raise


if __name__ == "__main__":
    main()