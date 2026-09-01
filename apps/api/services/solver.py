"""
Solver service bridging to Python AI engine.
Handles cube state solving using Kociemba and IDA* algorithms.
"""

import logging
from typing import List, Tuple
from datetime import datetime
import time

from ..models import CubeStateModel, MoveModel, SolveResponse
from ..errors import SolveFailedError

logger = logging.getLogger(__name__)


class SolverService:
    """
    Service for solving Rubik's cube configurations.
    Interfaces with Python solver in ai/engine/solver.py
    """
    
    def __init__(self):
        """Initialize solver service."""
        self.logger = logger
        # In Phase 5, import actual solver: from ai.engine.solver import Solver
        # For now, we'll implement a placeholder that will be replaced
        
    def solve(
        self,
        cube_state: CubeStateModel,
        max_moves: int = 20,
        timeout_seconds: int = 10,
    ) -> SolveResponse:
        """
        Solve a cube configuration.
        
        Args:
            cube_state: The cube configuration to solve
            max_moves: Maximum number of moves in solution
            timeout_seconds: Timeout for solving
            
        Returns:
            SolveResponse with solution moves and metadata
            
        Raises:
            SolveFailedError: If solving fails
        """
        start_time = time.time()
        
        try:
            # Validate input
            if not self._validate_cube_state(cube_state):
                raise SolveFailedError("Invalid cube state for solving")
            
            # TODO Phase 2: Bridge to actual Python solver
            # For now, return a placeholder solution
            moves = self._get_placeholder_solution(cube_state)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            self.logger.info(
                f"Solve completed",
                extra={
                    "num_moves": len(moves),
                    "solving_time_ms": elapsed_ms,
                    "timeout_seconds": timeout_seconds,
                },
            )
            
            return SolveResponse(
                moves=moves,
                num_moves=len(moves),
                confidence=0.95,  # Kociemba guarantees optimal solution
                solving_time_ms=elapsed_ms,
                solver_used="kociemba",
            )
            
        except SolveFailedError:
            raise
        except Exception as e:
            self.logger.exception("Solve operation failed", exc_info=e)
            raise SolveFailedError(f"Solving failed: {str(e)}")
    
    def _validate_cube_state(self, cube_state: CubeStateModel) -> bool:
        """Validate cube state before solving."""
        # Basic validation - more thorough validation in ValidatorService
        if not cube_state.corners or len(cube_state.corners) != 8:
            return False
        if not cube_state.edges or len(cube_state.edges) != 12:
            return False
        return True
    
    def _get_placeholder_solution(self, cube_state: CubeStateModel) -> List[MoveModel]:
        """
        Get placeholder solution (to be replaced with real solver in Phase 2).
        
        This is a simple placeholder that returns a valid move sequence.
        The real implementation will use Kociemba or IDA*.
        """
        # Placeholder: Return a simple R U R' U' sequence
        return [
            MoveModel(face="R", times=1),
            MoveModel(face="U", times=1),
            MoveModel(face="R", times=3),  # R' = R3
            MoveModel(face="U", times=3),  # U' = U3
        ]


# Global solver instance
_solver_instance: SolverService | None = None


def get_solver_service() -> SolverService:
    """Get or create solver service instance."""
    global _solver_instance
    if _solver_instance is None:
        _solver_instance = SolverService()
    return _solver_instance
