"""
Cube solving endpoints.
Provides REST API for solving Rubik's cube configurations.
"""

import logging
from fastapi import APIRouter, status

from ..models import SolveRequest, SolveResponse
from ..services import get_solver_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["solver"])


@router.post(
    "/solve",
    response_model=SolveResponse,
    status_code=status.HTTP_200_OK,
    summary="Solve a Rubik's cube",
    responses={
        200: {"description": "Solution found"},
        400: {"description": "Invalid cube state"},
        422: {"description": "Unsolvable or timeout"},
    },
)
async def solve_cube(request: SolveRequest) -> SolveResponse:
    """
    Solve a Rubik's cube configuration.
    
    Takes a cube state (corners and edges with their orientations) and returns
    an optimal or near-optimal solution using Kociemba or IDA* algorithm.
    
    **Cube State Representation:**
    - `corners`: 8-element list of corner positions (0-7)
    - `corner_orientations`: 8-element list of corner rotations (0-2)
    - `edges`: 12-element list of edge positions (0-11)
    - `edge_orientations`: 12-element list of edge flips (0-1)
    
    **Response:**
    - `moves`: List of moves in standard Rubik's notation (U, D, F, B, L, R with `, 2 modifiers)
    - `num_moves`: Total number of moves in solution
    - `confidence`: Solution quality (1.0 = optimal)
    - `solving_time_ms`: Time taken to compute solution
    - `solver_used`: Algorithm used ("kociemba", "ida", etc.)
    
    **Example:**
    ```json
    {
        "cube_state": {
            "corners": [0, 1, 2, 3, 4, 5, 6, 7],
            "corner_orientations": [0, 0, 0, 0, 0, 0, 0, 0],
            "edges": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "edge_orientations": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        },
        "max_moves": 20
    }
    ```
    """
    solver = get_solver_service()
    return solver.solve(
        cube_state=request.cube_state,
        max_moves=request.max_moves or 20,
    )
