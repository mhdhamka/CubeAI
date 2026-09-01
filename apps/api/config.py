"""
Configuration management for CubeAI API service.
Handles environment-based settings for development, testing, and production.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """API configuration loaded from environment variables."""

    # Service
    SERVICE_NAME: str = "CubeAI API"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # Database
    DATABASE_URL: Optional[str] = "postgresql://cube:cube@localhost:5432/cube_ai"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # API Configuration
    REQUEST_TIMEOUT: int = 30  # seconds
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Vision Service
    VISION_CONFIDENCE_THRESHOLD: float = 0.7
    SCAN_MAX_RETRIES: int = 3
    
    # Solver
    SOLVER_MAX_MOVES: int = 20
    SOLVER_TIMEOUT: int = 10  # seconds
    
    # Coaching
    COACHING_PROVIDER: str = "deterministic"  # "deterministic" or "external"
    COACHING_EXTERNAL_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get settings instance with validation."""
    return Settings()


# Global settings instance
settings = get_settings()
