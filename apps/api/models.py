"""
Shared data models and types for CubeAI API.
Includes request/response schemas and domain models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status: 'healthy' or 'degraded'")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CubeStateModel(BaseModel):
    """Cube state representation as corner and edge permutations/orientations."""
    
    # Corner permutation (8 corners, 0-7)
    corners: List[int] = Field(..., min_items=8, max_items=8, description="Corner positions")
    
    # Corner orientations (0-2 for each corner)
    corner_orientations: List[int] = Field(..., min_items=8, max_items=8, description="Corner orientations")
    
    # Edge permutation (12 edges, 0-11)
    edges: List[int] = Field(..., min_items=12, max_items=12, description="Edge positions")
    
    # Edge orientations (0-1 for each edge)
    edge_orientations: List[int] = Field(..., min_items=12, max_items=12, description="Edge orientations")


class MoveModel(BaseModel):
    """Rubik's cube move representation."""
    
    face: str = Field(..., regex="^[UDFBLR]$", description="Face: U/D/F/B/L/R")
    times: int = Field(default=1, ge=1, le=3, description="Number of 90° rotations (1-3)")
    
    @property
    def notation(self) -> str:
        """Get standard notation for this move."""
        if self.times == 1:
            return self.face
        elif self.times == 2:
            return f"{self.face}2"
        elif self.times == 3:
            return f"{self.face}'"
        return self.face


class SolveRequest(BaseModel):
    """Request to solve a cube."""
    
    cube_state: CubeStateModel
    max_moves: Optional[int] = Field(default=20, ge=1, le=50)


class SolveResponse(BaseModel):
    """Solution response."""
    
    moves: List[MoveModel]
    num_moves: int
    confidence: float = Field(ge=0.0, le=1.0)
    solving_time_ms: int
    solver_used: str = Field(default="kociemba")


class ValidateRequest(BaseModel):
    """Request to validate a cube state."""
    
    cube_state: CubeStateModel


class ValidationError(BaseModel):
    """Validation error detail."""
    
    field: str
    error: str


class ValidateResponse(BaseModel):
    """Validation response."""
    
    valid: bool
    errors: List[ValidationError] = []
    is_solved: bool = False
    scramble_distance: Optional[int] = None  # Minimum moves to solve


class ScanImageRequest(BaseModel):
    """Request to scan image for cube state."""
    
    # Image data will be handled as multipart/form-data
    # This model is for documentation purposes
    pass


class ScanMetadata(BaseModel):
    """Metadata for scan results."""
    
    confidence: float = Field(ge=0.0, le=1.0)
    detected_faces: int = Field(ge=1, le=6)
    processing_time_ms: int
    model_version: str


class ScanResponse(BaseModel):
    """Response from image scan."""
    
    cube_state: CubeStateModel
    metadata: ScanMetadata
    validation: ValidateResponse


class ProfileModel(BaseModel):
    """User's cubing profile/identity."""
    
    id: Optional[int] = None
    user_id: int
    name: str = Field(..., min_length=1, max_length=100)
    cube_size: int = Field(default=3, ge=2, le=10)
    solving_method: str = Field(default="cfop", max_length=50)  # cfop, roux, petrus, zz
    preferred_focus: str = Field(default="overall", max_length=50)  # cross, f2l, oll, pll, overall
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SolveRecordModel(BaseModel):
    """Single solve record."""
    
    id: Optional[int] = None
    profile_id: int
    time_ms: int = Field(ge=0, description="Solve time in milliseconds")
    num_moves: int = Field(ge=1, description="Number of moves in solution")
    scramble: str = Field(..., description="Scramble notation")
    solution: str = Field(..., description="Solution notation")
    solver_used: str = Field(default="manual", max_length=50)  # manual, kociemba, human, algorithm
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_dnf: bool = Field(default=False, description="Did Not Finish")
    is_dns: bool = Field(default=False, description="Did Not Start")
    notes: Optional[str] = Field(None, max_length=500)
    metadata: Optional[dict] = Field(None, description="Additional JSON metadata")
    created_at: Optional[datetime] = None


class StatisticsModel(BaseModel):
    """Aggregated solve statistics."""
    
    profile_id: int
    total_solves: int
    best_time_ms: Optional[int] = None
    worst_time_ms: Optional[int] = None
    average_ao5_ms: Optional[float] = None  # Average of 5
    average_ao12_ms: Optional[float] = None  # Average of 12
    average_ao100_ms: Optional[float] = None  # Average of 100
    average_overall_ms: Optional[float] = None  # Overall average


class CoachingRequest(BaseModel):
    """Request for coaching/explanation."""
    
    cube_state: CubeStateModel
    solution_moves: List[MoveModel]
    focus: Optional[str] = Field(None, description="Focus area: 'cross', 'f2l', 'oll', 'pll', 'overall'")


class CoachingResponse(BaseModel):
    """Coaching response with explanations."""
    
    explanation: str
    key_points: List[str]
    suggested_algorithms: List[str] = []
    difficulty_level: str = Field(description="beginner, intermediate, advanced")
