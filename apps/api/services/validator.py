"""
Cube state validation service.
Validates cube configurations for physical possibility and solvability.
"""

import logging
from typing import List, Optional

from ..models import (
    CubeStateModel,
    ValidateResponse,
    ValidationError,
)
from ..errors import InvalidCubeStateError

logger = logging.getLogger(__name__)


class ValidatorService:
    """
    Service for validating Rubik's cube states.
    Interfaces with Python validator in ai/engine/cubeValidator.py
    """
    
    def __init__(self):
        """Initialize validator service."""
        self.logger = logger
        
    def validate(self, cube_state: CubeStateModel) -> ValidateResponse:
        """
        Validate a cube state for physical possibility.
        
        A valid cube state must have:
        - 8 corners with valid permutations (0-7) and orientations (0-2)
        - 12 edges with valid permutations (0-11) and orientations (0-1)
        - Valid permutation parity
        - Valid total corner and edge orientation mod 3 and 2
        
        Args:
            cube_state: The cube configuration to validate
            
        Returns:
            ValidateResponse with validation results
        """
        errors: List[ValidationError] = []
        
        # Validate corner permutation
        if len(cube_state.corners) != 8:
            errors.append(ValidationError(
                field="corners",
                error=f"Expected 8 corners, got {len(cube_state.corners)}"
            ))
        elif not self._validate_permutation(cube_state.corners, 8):
            errors.append(ValidationError(
                field="corners",
                error="Corner permutation invalid (must be 0-7 in valid order)"
            ))
        
        # Validate corner orientations
        if len(cube_state.corner_orientations) != 8:
            errors.append(ValidationError(
                field="corner_orientations",
                error=f"Expected 8 orientations, got {len(cube_state.corner_orientations)}"
            ))
        elif not all(0 <= o <= 2 for o in cube_state.corner_orientations):
            errors.append(ValidationError(
                field="corner_orientations",
                error="Corner orientations must be 0, 1, or 2"
            ))
        elif sum(cube_state.corner_orientations) % 3 != 0:
            errors.append(ValidationError(
                field="corner_orientations",
                error="Sum of corner orientations must be divisible by 3"
            ))
        
        # Validate edge permutation
        if len(cube_state.edges) != 12:
            errors.append(ValidationError(
                field="edges",
                error=f"Expected 12 edges, got {len(cube_state.edges)}"
            ))
        elif not self._validate_permutation(cube_state.edges, 12):
            errors.append(ValidationError(
                field="edges",
                error="Edge permutation invalid (must be 0-11 in valid order)"
            ))
        
        # Validate edge orientations
        if len(cube_state.edge_orientations) != 12:
            errors.append(ValidationError(
                field="edge_orientations",
                error=f"Expected 12 orientations, got {len(cube_state.edge_orientations)}"
            ))
        elif not all(0 <= o <= 1 for o in cube_state.edge_orientations):
            errors.append(ValidationError(
                field="edge_orientations",
                error="Edge orientations must be 0 or 1"
            ))
        elif sum(cube_state.edge_orientations) % 2 != 0:
            errors.append(ValidationError(
                field="edge_orientations",
                error="Sum of edge orientations must be even"
            ))
        
        # Validate permutation parity (corners and edges must have same parity)
        if not errors and self._get_permutation_parity(cube_state.corners) != \
           self._get_permutation_parity(cube_state.edges):
            errors.append(ValidationError(
                field="permutation",
                error="Corner and edge permutation parity mismatch"
            ))
        
        is_valid = len(errors) == 0
        is_solved = is_valid and self._is_solved(cube_state)
        scramble_distance = self._estimate_scramble_distance(cube_state) if is_valid else None
        
        self.logger.info(
            f"Cube validation: {'valid' if is_valid else 'invalid'}",
            extra={
                "errors_count": len(errors),
                "is_solved": is_solved,
                "scramble_distance": scramble_distance,
            },
        )
        
        return ValidateResponse(
            valid=is_valid,
            errors=errors,
            is_solved=is_solved,
            scramble_distance=scramble_distance,
        )
    
    def _validate_permutation(self, perm: List[int], size: int) -> bool:
        """
        Validate that a permutation contains exactly 0..size-1.
        """
        if len(perm) != size:
            return False
        return sorted(perm) == list(range(size))
    
    def _get_permutation_parity(self, perm: List[int]) -> int:
        """
        Calculate permutation parity (0 for even, 1 for odd).
        Uses cycle decomposition counting.
        """
        visited = [False] * len(perm)
        num_cycles = 0
        
        for i in range(len(perm)):
            if not visited[i]:
                j = i
                while not visited[j]:
                    visited[j] = True
                    j = perm[j]
                num_cycles += 1
        
        # Parity = (n - num_cycles) % 2
        return (len(perm) - num_cycles) % 2
    
    def _is_solved(self, cube_state: CubeStateModel) -> bool:
        """
        Check if cube is in solved state (identity permutation + no orientations).
        """
        corners_solved = (
            cube_state.corners == list(range(8)) and
            all(o == 0 for o in cube_state.corner_orientations)
        )
        edges_solved = (
            cube_state.edges == list(range(12)) and
            all(o == 0 for o in cube_state.edge_orientations)
        )
        return corners_solved and edges_solved
    
    def _estimate_scramble_distance(self, cube_state: CubeStateModel) -> int:
        """
        Estimate minimum moves to solve (God's number).
        TODO Phase 2: Use actual Kociemba distance tables.
        For now, return a heuristic estimate based on permutation disorder.
        """
        if self._is_solved(cube_state):
            return 0
        
        # Count position differences (heuristic)
        corner_disorder = sum(
            1 for i, c in enumerate(cube_state.corners) if c != i
        )
        edge_disorder = sum(
            1 for i, e in enumerate(cube_state.edges) if e != i
        )
        
        # Very rough heuristic: ~2 moves per disordered piece
        estimate = max(corner_disorder, edge_disorder)
        return min(estimate + 2, 20)  # Cap at 20 moves


# Global validator instance
_validator_instance: ValidatorService | None = None


def get_validator_service() -> ValidatorService:
    """Get or create validator service instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ValidatorService()
    return _validator_instance
