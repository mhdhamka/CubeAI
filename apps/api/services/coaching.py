"""
Coaching service for providing cubing guidance and algorithm explanations.
Bridges to Python coaching logic in ai/coach/.
"""

import logging
from typing import Optional

from ..models import (
    CubeStateModel,
    MoveModel,
    CoachingRequest,
    CoachingResponse,
)

logger = logging.getLogger(__name__)


class CoachingService:
    """
    Service for providing personalized coaching and algorithm guidance.
    Interfaces with Python coaching pipeline in ai/coach/
    """
    
    def __init__(self):
        """Initialize coaching service."""
        self.logger = logger
        
    def get_coaching(self, request: CoachingRequest) -> CoachingResponse:
        """
        Get coaching explanation for a solution.
        
        Provides contextual guidance including:
        - Solution explanation
        - Key learning points
        - Suggested algorithms
        - Difficulty assessment
        
        Args:
            request: Coaching request with cube state, solution, and focus
            
        Returns:
            CoachingResponse with explanation and guidance
        """
        focus = request.focus or 'overall'
        
        self.logger.info(
            f"Coaching requested",
            extra={
                "focus": focus,
                "solution_length": len(request.solution_moves),
            },
        )
        
        # TODO Phase 6: Bridge to Python coaching pipeline (ai/coach/coach.py)
        # Real implementation will:
        # 1. Parse solution moves
        # 2. Identify algorithms used
        # 3. Provide step-by-step explanation
        # 4. Suggest improvements or alternative approaches
        # 5. Identify learning opportunities
        
        return self._get_deterministic_coaching(request)
    
    def _get_deterministic_coaching(self, request: CoachingRequest) -> CoachingResponse:
        """
        Get deterministic coaching (fallback/default implementation).
        This runs without external reasoning service.
        """
        focus = request.focus or 'overall'
        solution_length = len(request.solution_moves)
        
        # Determine difficulty level based on number of moves
        if solution_length <= 8:
            difficulty = 'beginner'
        elif solution_length <= 15:
            difficulty = 'intermediate'
        else:
            difficulty = 'advanced'
        
        # Build coaching response based on focus area
        if focus == 'cross':
            return CoachingResponse(
                explanation="The cross is the first step of the CFOP (Fridrich) method. "
                            "Your solution uses the bottom-up approach, starting with edge placement. "
                            "The cross typically requires 6-8 moves.",
                key_points=[
                    "Look ahead while solving the cross",
                    "Minimize rotations of the entire cube",
                    "Plan edge pairs before executing",
                    "Use M-slice moves efficiently (middle layer rotations)",
                ],
                suggested_algorithms=[
                    "Rw U' R U Rw'",
                    "U R U' R'",
                    "M' U M",
                ],
                difficulty_level=difficulty,
            )
        elif focus == 'f2l':
            return CoachingResponse(
                explanation="F2L (First 2 Layers) combines the white cross with the first layer corners "
                            "and second layer edges into one integrated step. "
                            f"Your solution uses {solution_length} moves total for this phase.",
                key_points=[
                    "Pair corners with their edge partners",
                    "Use cube rotations as setup moves",
                    "Practice the 41 F2L cases",
                    "Develop rotationless solutions for common cases",
                ],
                suggested_algorithms=[
                    "R U R' U'",
                    "y' R U' R'",
                    "U R U' R' U R U' R'",
                ],
                difficulty_level=difficulty,
            )
        elif focus == 'oll':
            return CoachingResponse(
                explanation="OLL (Orient Last Layer) positions the yellow stickers on top "
                            "without worrying about placement. "
                            "There are 57 cases to master for speedcubing.",
                key_points=[
                    "Learn the 57 OLL algorithms",
                    "Start with the 2-look method (9 cases)",
                    "Recognize patterns quickly",
                    "Practice lookahead during F2L into OLL",
                ],
                suggested_algorithms=[
                    "F (R U R' U') F'",
                    "R U2 R2' F R F'",
                    "(R U R' U)3",
                ],
                difficulty_level="advanced" if difficulty == 'advanced' else "intermediate",
            )
        elif focus == 'pll':
            return CoachingResponse(
                explanation="PLL (Permute Last Layer) is the final step, placing the yellow stickers "
                            "in their correct positions. There are 21 cases.",
                key_points=[
                    "Learn the 21 PLL algorithms",
                    "Start with 2-look method (6 cases + identity)",
                    "Use AUF (Alignment Up Face) efficiently",
                    "Recognize parity and cycle patterns",
                ],
                suggested_algorithms=[
                    "R' U R U' R' U' R U R' U R U2 R'",  # T-perm
                    "x' R U' R D2 R' U R D2 R2",  # Ax-perm
                    "M2 U M2 U2 M2 U M2",  # M-slice PLL
                ],
                difficulty_level="advanced",
            )
        else:  # overall
            return CoachingResponse(
                explanation=f"You solved the cube in {solution_length} moves! "
                            "Here's an overview of your solution's efficiency and technique. "
                            "The Fridrich/CFOP method (Cross, F2L, OLL, PLL) is the most popular speedcubing method.",
                key_points=[
                    f"Solution efficiency: {self._estimate_efficiency(solution_length)}",
                    "Practice look-ahead during each step",
                    "Reduce rotations and finger-tricks",
                    "Build muscle memory for common cases",
                    "Track your improvement over time",
                ],
                suggested_algorithms=[
                    "R U R' U'",
                    "R U2 R'",
                    "R' U' R U",
                ],
                difficulty_level=difficulty,
            )
    
    def _estimate_efficiency(self, moves: int) -> str:
        """Estimate solution efficiency based on move count."""
        if moves <= 6:
            return "Excellent - Very efficient solution"
        elif moves <= 12:
            return "Good - Solid technique"
        elif moves <= 20:
            return "Fair - Some optimization possible"
        else:
            return "Practice needed - Work on reducing moves"


# Global coaching service instance
_coaching_instance: CoachingService | None = None


def get_coaching_service() -> CoachingService:
    """Get or create coaching service instance."""
    global _coaching_instance
    if _coaching_instance is None:
        _coaching_instance = CoachingService()
    return _coaching_instance
