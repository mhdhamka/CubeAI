"""
Cube validation endpoints.
Provides REST API for validating Rubik's cube configurations.
"""

import logging
from fastapi import APIRouter, status

from ..models import ValidateRequest, ValidateResponse
from ..services import get_validator_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["validation"])


@router.post(
    "/validate",
    response_model=ValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate a Rubik's cube state",
    responses={
        200: {"description": "Validation result returned"},
        400: {"description": "Invalid request"},
    },
)
async def validate_cube(request: ValidateRequest) -> ValidateResponse:
    """
    Validate a Rubik's cube configuration for physical possibility.
    
    Checks:
    - Valid corner permutation (0-7) and orientations (0-2)
    - Valid edge permutation (0-11) and orientations (0-1)
    - Valid parity (corner and edge permutation parity match)
    - Valid orientation sums (corners mod 3 = 0, edges mod 2 = 0)
    - Physical solvability
    
    **Cube State Representation:**
    - `corners`: 8-element list of corner positions (0-7)
    - `corner_orientations`: 8-element list of corner rotations (0-2)
    - `edges`: 12-element list of edge positions (0-11)
    - `edge_orientations`: 12-element list of edge flips (0-1)
    
    **Response:**
    - `valid`: Whether the cube state is physically possible
    - `errors`: List of validation errors (empty if valid)
    - `is_solved`: Whether the cube is in the solved state
    - `scramble_distance`: Estimated minimum moves to solve (if valid)
    
    **Example Request:**
    ```json
    {
        "cube_state": {
            "corners": [0, 1, 2, 3, 4, 5, 6, 7],
            "corner_orientations": [0, 0, 0, 0, 0, 0, 0, 0],
            "edges": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "edge_orientations": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
    }
    ```
    
    **Example Response (Valid & Solved):**
    ```json
    {
        "valid": true,
        "errors": [],
        "is_solved": true,
        "scramble_distance": 0
    }
    ```
    
    **Example Response (Invalid):**
    ```json
    {
        "valid": false,
        "errors": [
            {
                "field": "corners",
                "error": "Corner permutation invalid (must be 0-7 in valid order)"
            }
        ],
        "is_solved": false,
        "scramble_distance": null
    }
    ```
    """
    validator = get_validator_service()
    return validator.validate(request.cube_state)
