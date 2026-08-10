
"""
CubeAI - Rubik's Cube Color Classifier

Classifies Rubik's Cube sticker colors from image regions.

The classifier uses:
1. Center-region sampling
2. HSV color space
3. Robust median/percentile statistics
4. Saturation/value checks
5. Explicit color distance scoring
6. Brightness normalization
7. Confidence scoring

Supported colors:
    white
    yellow
    red
    orange
    green
    blue
    unknown

This module is designed to work with:
    ai/vision/faceDetector.py
    ai/vision/scanner.py
"""

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


# ============================================================
# Types
# ============================================================

@dataclass
class ColorResult:
    color: str
    confidence: float
    hsv: tuple[float, float, float]


# ============================================================
# Colors
# ============================================================

WHITE = "white"
YELLOW = "yellow"
RED = "red"
ORANGE = "orange"
GREEN = "green"
BLUE = "blue"
UNKNOWN = "unknown"


# ============================================================
# Color definitions
# ============================================================

# HSV hue values in OpenCV:
#
#   0   = red
#   15  = orange
#   30  = yellow
#   60  = green
#   112 = blue
#
# Hue range:
#   0 - 179
#
# These are intentionally broad because real cube stickers
# are affected by lighting, camera white balance, shadows,
# reflections, and image compression.

COLOR_CENTERS = {
    WHITE: {
        "hue": None,
        "saturation": 25.0,
        "value": 210.0,
    },
    YELLOW: {
        "hue": 30.0,
        "saturation": 180.0,
        "value": 190.0,
    },
    RED: {
        "hue": 0.0,
        "saturation": 180.0,
        "value": 150.0,
    },
    ORANGE: {
        "hue": 15.0,
        "saturation": 180.0,
        "value": 180.0,
    },
    GREEN: {
        "hue": 65.0,
        "saturation": 150.0,
        "value": 140.0,
    },
    BLUE: {
        "hue": 112.0,
        "saturation": 150.0,
        "value": 140.0,
    },
}


# ============================================================
# Helpers
# ============================================================

def _validate_image(image: np.ndarray) -> None:
    """
    Validate an image before classification.
    """

    if image is None:
        raise ValueError(
            "Image cannot be None."
        )

    if not isinstance(image, np.ndarray):
        raise TypeError(
            "Image must be a NumPy array."
        )

    if image.size == 0:
        raise ValueError(
            "Image cannot be empty."
        )

    if image.ndim not in (2, 3):
        raise ValueError(
            "Image must have 2 or 3 dimensions."
        )


def _center_crop(
    image: np.ndarray,
    ratio: float = 0.50,
) -> np.ndarray:
    """
    Extract the center portion of a sticker.

    The center is preferred because sticker borders may
    contain black plastic, shadows, reflections, or grid lines.
    """

    if ratio <= 0.0 or ratio > 1.0:
        raise ValueError(
            "Crop ratio must be between 0 and 1."
        )

    height, width = image.shape[:2]

    crop_width = max(
        1,
        int(width * ratio),
    )

    crop_height = max(
        1,
        int(height * ratio),
    )

    x1 = (
        width - crop_width
    ) // 2

    y1 = (
        height - crop_height
    ) // 2

    x2 = x1 + crop_width
    y2 = y1 + crop_height

    cropped = image[
        y1:y2,
        x1:x2,
    ]

    if cropped.size == 0:
        raise ValueError(
            "Center crop produced an empty image."
        )

    return cropped


def _circular_hue_distance(
    value: float,
    center: float,
) -> float:
    """
    Calculate circular distance between HSV hue values.
    """

    difference = abs(
        value - center
    )

    return min(
        difference,
        180.0 - difference,
    )


def _circular_hue_confidence(
    value: float,
    center: float,
    tolerance: float,
) -> float:
    """
    Convert circular hue distance into confidence.
    """

    distance = _circular_hue_distance(
        value,
        center,
    )

    if tolerance <= 0:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            1.0 - (
                distance / tolerance
            ),
        ),
    )


def _hue_confidence(
    value: float,
    center: float,
    tolerance: float,
) -> float:
    """
    Convert normal hue distance into confidence.
    """

    distance = abs(
        value - center
    )

    if tolerance <= 0:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            1.0 - (
                distance / tolerance
            ),
        ),
    )


def _safe_float(value) -> float:
    """
    Convert a NumPy value into a normal Python float.
    """

    return float(value)


# ============================================================
# Image statistics
# ============================================================

def _get_hsv_statistics(
    image: np.ndarray,
) -> tuple[float, float, float]:
    """
    Calculate robust HSV statistics.

    Median is used instead of a simple average because
    reflections and dark borders can distort the mean.

    The middle 80% of pixels are used to reduce the impact
    of extreme highlights/shadows.
    """

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV,
    )

    pixels = hsv.reshape(
        -1,
        3,
    ).astype(np.float32)

    if len(pixels) == 0:
        raise ValueError(
            "No pixels available for HSV classification."
        )

    # Remove extreme brightness outliers.
    value_values = pixels[:, 2]

    lower_value = np.percentile(
        value_values,
        10,
    )

    upper_value = np.percentile(
        value_values,
        90,
    )

    mask = (
        (value_values >= lower_value)
        & (value_values <= upper_value)
    )

    filtered = pixels[mask]

    if len(filtered) < 5:
        filtered = pixels

    h = np.median(
        filtered[:, 0]
    )

    s = np.median(
        filtered[:, 1]
    )

    v = np.median(
        filtered[:, 2]
    )

    return (
        _safe_float(h),
        _safe_float(s),
        _safe_float(v),
    )


# ============================================================
# White detection
# ============================================================

def _classify_white(
    h: float,
    s: float,
    v: float,
) -> Optional[ColorResult]:
    """
    Detect white stickers.

    White is special because hue is unreliable when
    saturation is low.

    We therefore rely mainly on:
        - low saturation
        - sufficiently high brightness
    """

    if s > 95:
        return None

    if v < 120:
        return None

    saturation_score = max(
        0.0,
        min(
            1.0,
            1.0 - (s / 95.0),
        ),
    )

    brightness_score = max(
        0.0,
        min(
            1.0,
            (v - 120.0) / 135.0,
        ),
    )

    confidence = (
        saturation_score * 0.55
        + brightness_score * 0.45
    )

    if confidence < 0.25:
        return None

    return ColorResult(
        WHITE,
        float(confidence),
        (h, s, v),
    )


# ============================================================
# Saturated color scoring
# ============================================================

def _score_saturated_color(
    color: str,
    h: float,
    s: float,
    v: float,
) -> float:
    """
    Calculate confidence for a saturated color.

    The score combines:
        - hue similarity
        - saturation
        - brightness
    """

    definition = COLOR_CENTERS[color]

    center_hue = definition["hue"]

    if center_hue is None:
        return 0.0

    # Different colors get slightly different tolerances.
    tolerances = {
        RED: 12.0,
        ORANGE: 10.0,
        YELLOW: 15.0,
        GREEN: 28.0,
        BLUE: 25.0,
    }

    tolerance = tolerances[color]

    if color == RED:
        hue_score = (
            _circular_hue_confidence(
                h,
                center_hue,
                tolerance,
            )
        )
    else:
        hue_score = (
            _hue_confidence(
                h,
                center_hue,
                tolerance,
            )
        )

    # Saturation score.
    #
    # Real stickers are normally strongly saturated.
    # We don't require maximum saturation because lighting
    # can reduce it.
    saturation_score = max(
        0.0,
        min(
            1.0,
            (s - 45.0) / 130.0,
        ),
    )

    # Brightness score.
    brightness_score = max(
        0.0,
        min(
            1.0,
            (v - 45.0) / 150.0,
        ),
    )

    score = (
        hue_score * 0.65
        + saturation_score * 0.20
        + brightness_score * 0.15
    )

    return float(
        max(
            0.0,
            min(
                1.0,
                score,
            ),
        )
    )


# ============================================================
# Classification
# ============================================================

def classify_color(
    image: np.ndarray,
) -> ColorResult:
    """
    Classify one Rubik's Cube sticker.

    Parameters
    ----------
    image:
        BGR image containing one sticker.

    Returns
    -------
    ColorResult
        Detected color, confidence, and HSV statistics.
    """

    _validate_image(image)

    # Convert grayscale images to BGR.
    if image.ndim == 2:
        image = cv2.cvtColor(
            image,
            cv2.COLOR_GRAY2BGR,
        )

    # --------------------------------------------------------
    # Sample only the center of the sticker.
    # --------------------------------------------------------

    image = _center_crop(
        image,
        ratio=0.50,
    )

    # --------------------------------------------------------
    # Robust HSV statistics.
    # --------------------------------------------------------

    h, s, v = _get_hsv_statistics(
        image
    )

    # --------------------------------------------------------
    # White
    # --------------------------------------------------------

    white_result = _classify_white(
        h,
        s,
        v,
    )

    # --------------------------------------------------------
    # Score all saturated colors.
    # --------------------------------------------------------

    color_scores = {}

    for color in [
        RED,
        ORANGE,
        YELLOW,
        GREEN,
        BLUE,
    ]:

        color_scores[color] = (
            _score_saturated_color(
                color,
                h,
                s,
                v,
            )
        )

    # --------------------------------------------------------
    # Add white to competition when available.
    # --------------------------------------------------------

    if white_result is not None:

        color_scores[WHITE] = (
            white_result.confidence
        )

    # --------------------------------------------------------
    # Find best color.
    # --------------------------------------------------------

    if not color_scores:
        return ColorResult(
            UNKNOWN,
            0.0,
            (h, s, v),
        )

    ranked = sorted(
        color_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    best_color, best_score = ranked[0]

    second_score = (
        ranked[1][1]
        if len(ranked) > 1
        else 0.0
    )

    # --------------------------------------------------------
    # Ambiguity penalty
    #
    # If two colors are extremely close, reduce confidence.
    # This is particularly useful for:
    #
    #   red vs orange
    #   orange vs yellow
    # --------------------------------------------------------

    margin = (
        best_score
        - second_score
    )

    if margin < 0.10:
        best_score *= 0.75

    elif margin < 0.20:
        best_score *= 0.90

    # --------------------------------------------------------
    # Very low saturation colors should not be classified
    # as saturated colors with high confidence.
    # --------------------------------------------------------

    if (
        best_color != WHITE
        and s < 45
    ):

        return ColorResult(
            UNKNOWN,
            0.0,
            (h, s, v),
        )

    # --------------------------------------------------------
    # Very dark regions are unreliable.
    # --------------------------------------------------------

    if v < 40:

        return ColorResult(
            UNKNOWN,
            0.0,
            (h, s, v),
        )

    # --------------------------------------------------------
    # Final confidence.
    # --------------------------------------------------------

    confidence = max(
        0.0,
        min(
            1.0,
            best_score,
        ),
    )

    # Do not return unknown for reasonable sticker colors.
    if confidence < 0.25:

        return ColorResult(
            UNKNOWN,
            float(confidence),
            (h, s, v),
        )

    return ColorResult(
        best_color,
        float(confidence),
        (h, s, v),
    )


# ============================================================
# Batch helpers
# ============================================================

def classify_stickers(
    stickers: list[np.ndarray],
) -> list[ColorResult]:
    """
    Classify multiple sticker images.
    """

    if not stickers:
        raise ValueError(
            "Sticker list cannot be empty."
        )

    return [
        classify_color(sticker)
        for sticker in stickers
    ]


def get_color_names(
    results: list[ColorResult],
) -> list[str]:
    """
    Extract only color names from results.
    """

    return [
        result.color
        for result in results
    ]


# ============================================================
# BGR helper
# ============================================================

def classify_bgr(
    b: int,
    g: int,
    r: int,
) -> ColorResult:
    """
    Classify a single BGR color.

    A 40x40 image is used instead of a 1x1 pixel because
    classify_color() performs a center crop.
    """

    values = np.array(
        [
            b,
            g,
            r,
        ],
        dtype=np.int32,
    )

    values = np.clip(
        values,
        0,
        255,
    ).astype(np.uint8)

    image = np.full(
        (40, 40, 3),
        values,
        dtype=np.uint8,
    )

    return classify_color(
        image
    )


# ============================================================
# Debug helper
# ============================================================

def classify_bgr_samples(
    samples: dict[str, tuple[int, int, int]],
) -> None:
    """
    Print classification results for BGR samples.
    """

    print(
        "Color classifier test"
    )

    print(
        "---------------------"
    )

    for expected, bgr in samples.items():

        result = classify_bgr(
            *bgr
        )

        status = (
            "OK"
            if result.color == expected
            else "MISMATCH"
        )

        print(
            f"{expected:>7} -> "
            f"{result.color:<7} "
            f"confidence="
            f"{result.confidence:.2f} "
            f"HSV=("
            f"{result.hsv[0]:.1f}, "
            f"{result.hsv[1]:.1f}, "
            f"{result.hsv[2]:.1f}"
            f") "
            f"[{status}]"
        )


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":

    test_colors = {
        "white": (255, 255, 255),
        "yellow": (0, 255, 255),
        "red": (0, 0, 255),
        "orange": (0, 165, 255),
        "green": (0, 255, 0),
        "blue": (255, 0, 0),
    }

    classify_bgr_samples(
        test_colors
    )

