"""
CubeAI FastAPI Application.
Main entry point for the API service.
"""

import logging
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from .errors import APIException, ErrorDetail, ErrorCode
from .routes import health, solve, validate, scan, coaching, profiles, solves, statistics, ws
from .db import init_db

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    # Initialize database tables
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="API for CubeAI - Rubik's Cube Vision and Solver Platform",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Exception handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle API exceptions with structured responses."""
    logger.error(f"API Error: {exc.code} - {exc.message}", extra={"details": exc.details})
    
    error_detail = ErrorDetail(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        timestamp=datetime.utcnow().isoformat(),
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_detail.model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception("Unexpected error", exc_info=exc)
    
    error_detail = ErrorDetail(
        code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error",
        details={"error": str(exc)} if settings.DEBUG else None,
        timestamp=datetime.utcnow().isoformat(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_detail.model_dump(),
    )


# Include routers
app.include_router(health.router)
app.include_router(solve.router)
app.include_router(validate.router)
app.include_router(scan.router)
app.include_router(coaching.router)
app.include_router(profiles.router)
app.include_router(solves.router)
app.include_router(statistics.router)
app.include_router(ws.router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint providing service information."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
