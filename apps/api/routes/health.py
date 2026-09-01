"""
Health check and status endpoints.
"""

from fastapi import APIRouter, status
from datetime import datetime
from ..config import settings
from ..models import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint.
    
    Returns the service status, name, version, and timestamp.
    """
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        timestamp=datetime.utcnow(),
    )


@router.get("/ready", response_model=dict, status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Readiness check endpoint.
    
    Indicates if the service is ready to accept requests.
    Can be extended to check database connectivity, etc.
    """
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/live", response_model=dict, status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness check endpoint.
    
    Indicates if the service is still running (basic check).
    Used by orchestrators like Kubernetes.
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
