"""Optional MediaPipe tracking adapter for camera stability experiments."""

from __future__ import annotations

from typing import Any


class MediaPipeAdapter:
    """Lazy MediaPipe wrapper that exposes a stable ``process`` method."""

    def __init__(self, mode: str = "hands", **kwargs: Any) -> None:
        self.mode = mode
        self.kwargs = kwargs
        self._solution: Any = None

    def _load(self) -> None:
        if self._solution is not None:
            return
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError(
                "MediaPipe support requires the optional 'mediapipe' package."
            ) from exc
        if self.mode != "hands":
            raise ValueError("MediaPipeAdapter currently supports mode='hands'.")
        self._solution = mp.solutions.hands.Hands(**self.kwargs)

    def process(self, image: Any) -> Any:
        self._load()
        return self._solution.process(image)

    def close(self) -> None:
        if self._solution is not None:
            self._solution.close()