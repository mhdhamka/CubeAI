"""
Coaching and guidance endpoints.
Provides AI coaching explanations for cube solutions.
"""

import logging
from fastapi import APIRouter, status

from ..models import CoachingRequest, CoachingResponse
from ..services import get_coaching_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["coaching"])


@router.post(
    "/coaching",
    response_model=CoachingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get coaching for a solution",
    responses={
        200: {"description": "Coaching explanation provided"},
        400: {"description": "Invalid request"},
    },
)
async def get_coaching(request: CoachingRequest) -> CoachingResponse:
    """
    Get personalized coaching and guidance for a cube solution.
    
    Provides contextual explanations including:
    - Solution breakdown and efficiency analysis
    - Key learning points and techniques
    - Suggested algorithms to practice
    - Difficulty level assessment
    - Focus-area specific guidance
    
    **Focus Areas:**
    - `cross`: Understanding the first layer cross strategy
    - `f2l`: First Two Layers technique and pair strategies
    - `oll`: Orient Last Layer case recognition and algorithms
    - `pll`: Permute Last Layer algorithms and execution
    - `overall`: General solution analysis and efficiency
    
    **Request Example:**
    ```json
    {
        "cube_state": {
            "corners": [0, 1, 2, 3, 4, 5, 6, 7],
            "corner_orientations": [0, 0, 0, 0, 0, 0, 0, 0],
            "edges": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "edge_orientations": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        },
        "solution_moves": [
            {"face": "R", "times": 1},
            {"face": "U", "times": 1},
            {"face": "R", "times": 3}
        ],
        "focus": "f2l"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "explanation": "F2L (First 2 Layers) combines the white cross with the first layer corners...",
        "key_points": [
            "Pair corners with their edge partners",
            "Use cube rotations as setup moves",
            "Practice the 41 F2L cases"
        ],
        "suggested_algorithms": [
            "R U R' U'",
            "y' R U' R'",
            "U R U' R' U R U' R'"
        ],
        "difficulty_level": "intermediate"
    }
    ```
    
    **Coaching Levels:**
    - `beginner`: Basic technique and first steps
    - `intermediate`: Standard method and case learning
    - `advanced`: Optimized algorithms and competitive speedcubing
    
    **Algorithm Format:**
    Standard Rubik's cube notation:
    - `U/D/F/B/L/R` - Face clockwise 90°
    - `U'/D'/F'/B'/L'/R'` - Face counter-clockwise 90°
    - `U2/D2/F2/B2/L2/R2` - Face 180°
    - `M/E/S` - Middle layer rotations
    - `x/y/z` - Cube rotations
    """
    coaching = get_coaching_service()
    return coaching.get_coaching(request)
