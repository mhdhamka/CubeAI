"""
Image scanning endpoints.
Provides REST API for scanning images and extracting cube states.
"""

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from ..config import settings
from ..models import ScanResponse
from ..services import get_vision_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["vision"])


@router.post(
    "/scan/image",
    response_model=ScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan an image for cube state",
    responses={
        200: {"description": "Cube state detected and validated"},
        400: {"description": "Invalid image format"},
        422: {"description": "Image processing failed or confidence too low"},
    },
)
async def scan_image(
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
) -> ScanResponse:
    """
    Scan a Rubik's cube image and extract the cube state.
    
    Accepts JPEG or PNG image of a Rubik's cube and returns the detected
    cube configuration with confidence metrics and validation results.
    
    **Processing Pipeline:**
    1. Image validation (format, size, quality)
    2. Cube detection (locate cube in image)
    3. Face detection (identify visible faces)
    4. Sticker identification (detect individual sticker colors)
    5. State building (construct CubeState from stickers)
    6. Validation (verify physical possibility)
    
    **Response Metadata:**
    - `confidence`: Detection confidence (0.0-1.0)
    - `detected_faces`: Number of cube faces detected (1-6)
    - `processing_time_ms`: Processing duration
    - `model_version`: Vision model version used
    
    **Example Response:**
    ```json
    {
        "cube_state": {
            "corners": [0, 1, 2, 3, 4, 5, 6, 7],
            "corner_orientations": [0, 0, 0, 0, 0, 0, 0, 0],
            "edges": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "edge_orientations": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        },
        "metadata": {
            "confidence": 0.94,
            "detected_faces": 3,
            "processing_time_ms": 245,
            "model_version": "1.0.0"
        },
        "validation": {
            "valid": true,
            "errors": [],
            "is_solved": true,
            "scramble_distance": 0
        }
    }
    ```
    
    **Error Responses:**
    - `INVALID_IMAGE`: Image format not supported or corrupted
    - `SCAN_FAILED`: Face/sticker detection failed
    - `LOW_CONFIDENCE`: Detection confidence below threshold
    - `INVALID_CUBE_STATE`: Detected state is not physically possible
    """
    vision = get_vision_service()
    
    uploads = files or ([file] if file is not None else [])
    if not uploads:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload one or more face images using the 'files' field.",
        )
    if len(uploads) > 6:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="A cube scan accepts at most six face images.",
        )

    image_data = []
    for upload in uploads:
        data = await upload.read(settings.MAX_UPLOAD_SIZE + 1)
        if len(data) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"{upload.filename or 'Image'} exceeds the 10 MB upload limit.",
            )
        image_data.append(data)
    
    # Scan image and return result
    return await vision.scan_image(image_data)
