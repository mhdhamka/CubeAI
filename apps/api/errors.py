"""
Error handling and exception definitions for CubeAI API.
Provides structured error responses and exception types.
"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel
from fastapi import status


class ErrorCode(str, Enum):
    """Enumeration of API error codes."""
    
    # Validation errors
    INVALID_CUBE_STATE = "INVALID_CUBE_STATE"
    INVALID_MOVE = "INVALID_MOVE"
    INVALID_IMAGE = "INVALID_IMAGE"
    
    # Vision errors
    SCAN_FAILED = "SCAN_FAILED"
    DETECTION_FAILED = "DETECTION_FAILED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    
    # Solver errors
    SOLVE_FAILED = "SOLVE_FAILED"
    UNSOLVABLE = "UNSOLVABLE"
    TIMEOUT = "TIMEOUT"
    
    # Persistence errors
    DATABASE_ERROR = "DATABASE_ERROR"
    NOT_FOUND = "NOT_FOUND"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorDetail(BaseModel):
    """Structured error detail response."""
    
    code: ErrorCode
    message: str
    details: Optional[dict[str, Any]] = None
    timestamp: Optional[str] = None


class APIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class InvalidCubeStateError(APIException):
    """Raised when cube state is invalid."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ErrorCode.INVALID_CUBE_STATE,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ScanFailedError(APIException):
    """Raised when image scanning fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ErrorCode.SCAN_FAILED,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class LowConfidenceError(APIException):
    """Raised when detection confidence is below threshold."""
    
    def __init__(self, confidence: float, threshold: float):
        super().__init__(
            code=ErrorCode.LOW_CONFIDENCE,
            message=f"Detection confidence {confidence:.2f} below threshold {threshold:.2f}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"confidence": confidence, "threshold": threshold},
        )


class SolveFailedError(APIException):
    """Raised when solving fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ErrorCode.SOLVE_FAILED,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class DatabaseError(APIException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class NotFoundError(APIException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=f"{resource} not found: {identifier}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)},
        )
