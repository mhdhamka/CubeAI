"""
Vision service for scanning cube images.
Bridges to Python vision pipeline in ai/vision/.
"""

import logging
import io
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
from PIL import Image

from ..config import settings
from ..errors import InvalidCubeStateError, LowConfidenceError, ScanFailedError
from ..models import CubeStateModel, ScanMetadata, ScanResponse
from .validator import get_validator_service
from .cube_state import to_api_cube_state, to_face_map

logger = logging.getLogger(__name__)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
VISION_DIR = REPOSITORY_ROOT / "ai" / "vision"
ENGINE_DIR = REPOSITORY_ROOT / "ai" / "engine"
for module_path in (VISION_DIR, ENGINE_DIR):
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))

from scanSession import CubeScanSession
from cubeStateBuilder import CubeStateBuilder
from cubieConverter import cubestate_to_cubiestate


class VisionService:
    """
    Service for processing images and extracting cube state.
    Interfaces with Python vision pipeline in ai/vision/
    """
    
    def __init__(self):
        """Initialize vision service."""
        self.logger = logger
        self.validator = get_validator_service()
        self.min_confidence = settings.VISION_CONFIDENCE_THRESHOLD

    def create_scan_session(self) -> CubeScanSession:
        """Create an isolated six-face scan session."""
        return CubeScanSession()

    def scan_face(self, session: CubeScanSession, image_data: bytes) -> Any:
        """Decode and scan one image, then add its detected face to a session."""
        image = self._load_image(image_data).convert("RGB")
        rgb = np.asarray(image)
        frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        previous_count = session.scanned_count()
        result = session.scan_image(frame)

        if not result.success:
            raise ScanFailedError(
                result.error or "Could not detect a cube face",
                details={"warnings": result.warnings or []},
            )

        if result.confidence < self.min_confidence:
            session.retry_face(result.face_name)
            raise ScanFailedError(
                f"Detection confidence {result.confidence:.2f} is below the {self.min_confidence:.2f} threshold",
                details={
                    "face": result.face_name,
                    "confidence": result.confidence,
                    "threshold": self.min_confidence,
                },
            )
        if session.scanned_count() == previous_count:
            raise ScanFailedError(
                f"Face {result.face_name} was already scanned; rotate the cube to a new face",
                details={"face": result.face_name, "scanned_faces": session.scanned_faces()},
            )

        return result

    def complete_scan(
        self,
        session: CubeScanSession,
        processing_time_ms: int,
    ) -> ScanResponse:
        """Build and physically validate the state from all six scanned faces."""
        result = session.build_result()
        if not result.success:
            raise ScanFailedError(
                result.error or "The cube scan is incomplete",
                details={
                    "scanned_faces": result.scanned_faces,
                    "missing_faces": result.missing_faces,
                    "color_counts": result.color_counts,
                    "warnings": result.warnings,
                },
            )

        if result.confidence < self.min_confidence:
            raise LowConfidenceError(result.confidence, self.min_confidence)

        built = CubeStateBuilder().build(
            {
                "faces": result.faces,
                "confidence": result.confidence,
                "complete": session.is_complete(),
            }
        )
        if not built.success or built.cube is None:
            raise ScanFailedError(
                "Detected stickers do not form a valid cube",
                details={
                    "errors": built.errors,
                    "warnings": built.warnings,
                    "scanned_faces": built.scanned_faces,
                    "missing_faces": built.missing_faces,
                },
            )

        try:
            cubies = cubestate_to_cubiestate(built.cube)
        except (TypeError, ValueError) as exc:
            raise InvalidCubeStateError(
                "Detected cube is physically invalid",
                details={"diagnostics": str(exc)},
            ) from exc

        cube_state = to_api_cube_state(cubies)
        validation = self.validator.validate(cube_state)
        if not validation.valid:
            raise InvalidCubeStateError(
                "Detected cube is physically invalid",
                details={"errors": [error.model_dump() for error in validation.errors]},
            )

        return ScanResponse(
            cube_state=cube_state,
            faces=to_face_map(built.cube),
            metadata=ScanMetadata(
                confidence=result.confidence,
                detected_faces=len(result.scanned_faces),
                processing_time_ms=processing_time_ms,
                model_version="cubeai-opencv-v1",
            ),
            validation=validation,
        )
        
    async def scan_image(self, image_data: bytes | Iterable[bytes]) -> ScanResponse:
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
        started_at = time.perf_counter()
        image_data_list = [image_data] if isinstance(image_data, bytes) else list(image_data)
        if not image_data_list:
            raise ScanFailedError("Upload at least one cube-face image")

        session = self.create_scan_session()
        try:
            for face_image in image_data_list:
                self.scan_face(session, face_image)
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            return self.complete_scan(session, elapsed_ms)
        except (ScanFailedError, LowConfidenceError, InvalidCubeStateError):
            raise
        except Exception as exc:
            self.logger.exception("Image scan failed", exc_info=exc)
            raise ScanFailedError(f"Failed to scan cube images: {exc}") from exc
    
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
    
# Global vision service instance
_vision_instance: VisionService | None = None


def get_vision_service() -> VisionService:
    """Get or create vision service instance."""
    global _vision_instance
    if _vision_instance is None:
        _vision_instance = VisionService()
    return _vision_instance
