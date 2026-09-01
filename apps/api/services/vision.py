"""
Vision service for scanning cube images.
Bridges to Python vision pipeline in ai/vision/.
"""

import logging
import io
import time
from typing import Optional
from PIL import Image
import numpy as np

from ..models import CubeStateModel, ScanMetadata, ScanResponse, ValidateResponse
from ..errors import ScanFailedError, LowConfidenceError
from .validator import get_validator_service

logger = logging.getLogger(__name__)


class VisionService:
    """
    Service for processing images and extracting cube state.
    Interfaces with Python vision pipeline in ai/vision/
    """
    
    def __init__(self):
        """Initialize vision service."""
        self.logger = logger
        self.validator = get_validator_service()
        self.min_confidence = 0.7
        
    async def scan_image(self, image_data: bytes) -> ScanResponse:
        """
        Scan an image and extract cube state.
        
        Args:
            image_data: Image file bytes (JPEG or PNG)
            
        Returns:
            ScanResponse with detected cube state and validation
            
        Raises:
            ScanFailedError: If image processing fails
            LowConfidenceError: If detection confidence is too low
        """
        start_time = time.time()
        
        try:
            # Parse image
            image = self._load_image(image_data)
            
            # TODO Phase 4: Bridge to Python vision pipeline
            # Real implementation will:
            # 1. Use ai/vision/cubeScanner.py to detect cube faces
            # 2. Use ai/vision/cubeDetector.py to identify stickers
            # 3. Use ai/vision/cubeStateBuilder.py to build CubeState
            # 4. Return confidence metrics
            
            # Placeholder: Return a solved cube state with high confidence
            cube_state = self._get_placeholder_cube_state()
            confidence = 0.95
            detected_faces = 6
            
            if confidence < self.min_confidence:
                raise LowConfidenceError(confidence, self.min_confidence)
            
            # Validate the detected state
            validation = self.validator.validate(cube_state)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            self.logger.info(
                "Image scan completed",
                extra={
                    "confidence": confidence,
                    "detected_faces": detected_faces,
                    "processing_time_ms": elapsed_ms,
                    "valid": validation.valid,
                },
            )
            
            return ScanResponse(
                cube_state=cube_state,
                metadata=ScanMetadata(
                    confidence=confidence,
                    detected_faces=detected_faces,
                    processing_time_ms=elapsed_ms,
                    model_version="1.0.0",
                ),
                validation=validation,
            )
            
        except (ScanFailedError, LowConfidenceError):
            raise
        except Exception as e:
            self.logger.exception("Image scan failed", exc_info=e)
            raise ScanFailedError(f"Failed to scan image: {str(e)}")
    
    def _load_image(self, image_data: bytes) -> Image.Image:
        """
        Load and validate image.
        
        Args:
            image_data: Image bytes
            
        Returns:
            PIL Image
            
        Raises:
            ScanFailedError: If image is invalid
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Validate image format
            if image.format not in ['JPEG', 'PNG', 'BMP', 'WEBP']:
                raise ScanFailedError(
                    f"Unsupported image format: {image.format}. Supported: JPEG, PNG, BMP, WEBP"
                )
            
            # Validate image size
            if image.size[0] < 100 or image.size[1] < 100:
                raise ScanFailedError(
                    f"Image too small: {image.size}. Minimum: 100x100"
                )
            
            if image.size[0] > 4096 or image.size[1] > 4096:
                raise ScanFailedError(
                    f"Image too large: {image.size}. Maximum: 4096x4096"
                )
            
            return image
            
        except ScanFailedError:
            raise
        except Exception as e:
            raise ScanFailedError(f"Failed to load image: {str(e)}")
    
    def _get_placeholder_cube_state(self) -> CubeStateModel:
        """
        Get placeholder cube state (solved cube).
        To be replaced with real vision pipeline in Phase 4.
        """
        return CubeStateModel(
            corners=list(range(8)),
            corner_orientations=[0] * 8,
            edges=list(range(12)),
            edge_orientations=[0] * 12,
        )


# Global vision service instance
_vision_instance: VisionService | None = None


def get_vision_service() -> VisionService:
    """Get or create vision service instance."""
    global _vision_instance
    if _vision_instance is None:
        _vision_instance = VisionService()
    return _vision_instance
