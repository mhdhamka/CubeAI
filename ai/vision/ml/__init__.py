"""Optional machine-learning vision adapters.

Adapters in this package follow the small ``detect(image)`` contract used by
the baseline OpenCV scanner. Optional ML dependencies are imported lazily.
"""

from .mediaPipeAdapter import MediaPipeAdapter
from .yoloDetector import YoloCubeDetector

__all__ = ["MediaPipeAdapter", "YoloCubeDetector"]