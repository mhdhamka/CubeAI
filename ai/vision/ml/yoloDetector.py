"""Optional YOLO cube detector adapter.

Install ``ultralytics`` only when this adapter is enabled. The baseline
OpenCV detector remains the default and is not imported from this module.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


class YoloCubeDetector:
    """Return the highest-confidence YOLO cube crop for the scanner."""

    def __init__(self, model_path: str, confidence: float = 0.5) -> None:
        self.model_path = model_path
        self.confidence = float(confidence)
        self._model: Any = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "YOLO support requires the optional 'ultralytics' package."
            ) from exc
        self._model = YOLO(self.model_path)

    def detect(self, image: np.ndarray) -> dict[str, Any]:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("YoloCubeDetector.detect() requires an image.")
        self._load()
        results = self._model.predict(source=image, conf=self.confidence, verbose=False)
        if not results or len(results[0].boxes) == 0:
            raise RuntimeError("YOLO did not detect a cube.")
        boxes = results[0].boxes
        index = int(boxes.conf.argmax().item())
        x1, y1, x2, y2 = boxes.xyxy[index].int().tolist()
        height, width = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            raise RuntimeError("YOLO returned an empty cube crop.")
        return {
            "image": crop,
            "confidence": float(boxes.conf[index].item()),
            "bbox": (x1, y1, x2 - x1, y2 - y1),
        }