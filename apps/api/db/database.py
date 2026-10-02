"""
Database connection management and session handling.
"""

from typing import Generator
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from ..config import settings
from .models import Base

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Additional connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using them
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to inject database session.
    
    Usage:
        @app.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Apply all versioned database migrations.
    """
    repository_root = Path(__file__).resolve().parents[3]
    config = Config(str(repository_root / "alembic.ini"))
    command.upgrade(config, "head")


def drop_db():
    """
    Drop all database tables.
    WARNING: This is destructive and should only be used in development.
    """
    Base.metadata.drop_all(bind=engine)


# SQLite-specific configuration
if settings.DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Enable foreign keys for SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
