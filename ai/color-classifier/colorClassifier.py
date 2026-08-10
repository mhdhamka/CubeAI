"""
CubeAI - Rubik's Cube Color Classifier

Classifies Rubik's Cube sticker colors from image regions using HSV.
"""

from dataclasses import dataclass
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
# Helpers
# ============================================================

def _validate_image(image: np.ndarray) -> None:
    if image is None:
        raise ValueError("Image cannot be None.")

    if not isinstance(image, np.ndarray):
        raise TypeError("Image must be a NumPy array.")

    if image.size == 0:
        raise ValueError("Image cannot be empty.")

    if image.ndim not in (2, 3):
        raise ValueError("Image must have 2 or 3 dimensions.")


def _center_crop(image: np.ndarray, ratio: float = 0.5) -> np.ndarray:
    height, width = image.shape[:2]

    crop_width = max(1, int(width * ratio))
    crop_height = max(1, int(height * ratio))

    x1 = (width - crop_width) // 2
    y1 = (height - crop_height) // 2

    x2 = x1 + crop_width
    y2 = y1 + crop_height

    cropped = image[y1:y2, x1:x2]

    if cropped.size == 0:
        raise ValueError("Center crop produced an empty image.")

    return cropped


def _hue_confidence(value: float, center: float, tolerance: float) -> float:
    distance = abs(value - center)
    return max(0.0, min(1.0, 1.0 - distance / tolerance))


def _circular_hue_confidence(value: float, center: float, tolerance: float) -> float:
    distance = min(abs(value - center), 180 - abs(value - center))
    return max(0.0, min(1.0, 1.0 - distance / tolerance))


# ============================================================
# Classification
# ============================================================

def classify_color(image: np.ndarray) -> ColorResult:
    _validate_image(image)

    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    image = _center_crop(image, ratio=0.5)

    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    pixels = hsv_image.reshape(-1, 3)
    median = np.median(pixels, axis=0)

    h, s, v = map(float, median)

    # White
    if s < 80 and v >= 150:
        confidence = min(1.0, max(0.0, (v - 150) / 105))
        return ColorResult(WHITE, confidence, (h, s, v))

    # Yellow
    if 20 <= h <= 40 and s >= 80 and v >= 80:
        return ColorResult(YELLOW, _hue_confidence(h, 30, 20), (h, s, v))

    # Red
    if h <= 10 or h >= 170:
        return ColorResult(RED, _circular_hue_confidence(h, 0, 10), (h, s, v))

    # Orange
    if 8 <= h <= 22 and s >= 80 and v >= 80:
        return ColorResult(ORANGE, _hue_confidence(h, 15, 7), (h, s, v))

    # Green
    if 40 <= h <= 90 and s >= 60 and v >= 50:
        return ColorResult(GREEN, _hue_confidence(h, 65, 25), (h, s, v))

    # Blue
    if 90 <= h <= 135 and s >= 60 and v >= 50:
        return ColorResult(BLUE, _hue_confidence(h, 112, 23), (h, s, v))

    return ColorResult(UNKNOWN, 0.0, (h, s, v))


# ============================================================
# Batch helpers
# ============================================================

def classify_stickers(stickers: list[np.ndarray]) -> list[ColorResult]:
    if not stickers:
        raise ValueError("Sticker list cannot be empty.")

    return [classify_color(sticker) for sticker in stickers]


def get_color_names(results: list[ColorResult]) -> list[str]:
    return [result.color for result in results]


# ============================================================
# BGR helper
# ============================================================

def classify_bgr(b: int, g: int, r: int) -> ColorResult:
    """
    Create a 40x40 BGR image instead of a 1x1 pixel.

    This prevents the center crop from producing an empty image.
    """

    image = np.full(
        (40, 40, 3),
        (b, g, r),
        dtype=np.uint8,
    )

    return classify_color(image)


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":
    print("CubeAI Color Classifier")
    print("-----------------------")

    test_colors = {
        "white": (255, 255, 255),
        "yellow": (0, 255, 255),
        "red": (0, 0, 255),
        "orange": (0, 165, 255),
        "green": (0, 255, 0),
        "blue": (255, 0, 0),
    }

    for name, (b, g, r) in test_colors.items():
        result = classify_bgr(b, g, r)

        print(
            f"{name:>7} -> "
            f"{result.color:<7} "
            f"confidence={result.confidence:.2f} "
            f"HSV={result.hsv}"
        )