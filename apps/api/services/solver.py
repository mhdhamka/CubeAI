"""
Solver service bridging to Python AI engine.
Handles cube state solving using Kociemba and IDA* algorithms.
"""

import logging
import time
from typing import List

from ..models import CubeStateInput, MoveModel, SolveResponse
from ..errors import SolveFailedError
from .cube_state import cubies_to_engine_cube, to_cubie_state
from solver import CubeSolver

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
        cube_state: CubeStateInput,
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
        try:
            cubie_state = to_cubie_state(cube_state)

            if cubie_state.is_solved():
                return SolveResponse(
                    moves=[],
                    num_moves=0,
                    confidence=1.0,
                    solving_time_ms=0,
                    solver_used="none",
                )

            engine_cube = cubies_to_engine_cube(cubie_state)
            solver = CubeSolver()
            started_at = time.perf_counter()
            solution = solver._solve_kociemba(engine_cube)
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)

            if not solver.verify_solution(engine_cube, solution):
                raise SolveFailedError(
                    "The solver returned moves that failed cube-state verification"
                )
            if len(solution) > max_moves:
                raise SolveFailedError(
                    f"The verified solution has {len(solution)} moves, exceeding the {max_moves}-move limit",
                    details={"num_moves": len(solution), "max_moves": max_moves},
                )

            moves = [
                MoveModel(face=move.face, times=move.quarter_turns)
                for move in solution
            ]
            
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
                confidence=1.0,
                solving_time_ms=elapsed_ms,
                solver_used="kociemba-two-phase",
            )
            
        except SolveFailedError:
            raise
        except Exception as e:
            self.logger.exception("Solve operation failed", exc_info=e)
            raise SolveFailedError(f"Solving failed: {str(e)}")
    
# Global solver instance
_solver_instance: SolverService | None = None


def get_solver_service() -> SolverService:
    """Get or create solver service instance."""
    global _solver_instance
    if _solver_instance is None:
        _solver_instance = SolverService()
    return _solver_instance
