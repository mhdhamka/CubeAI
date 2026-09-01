"""
SQLAlchemy models for CubeAI database schema.
Defines User, Profile, SolveRecord, and ScanSession tables.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profiles = relationship("Profile", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Profile(Base):
    """User's cubing profile/identity."""
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    cube_size = Column(Integer, default=3, nullable=False)  # 2x2, 3x3, 4x4, etc.
    solving_method = Column(String(50), default="cfop", nullable=False)  # cfop, roux, petrus, etc.
    preferred_focus = Column(String(50), default="overall")  # cross, f2l, oll, pll, overall
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profiles")
    solve_records = relationship("SolveRecord", back_populates="profile")
    scan_sessions = relationship("ScanSession", back_populates="profile")

    def __repr__(self):
        return f"<Profile(id={self.id}, name={self.name})>"


class SolveRecord(Base):
    """Individual cube solve attempt record."""
    __tablename__ = "solve_records"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    time_ms = Column(Integer, nullable=False)  # Solve time in milliseconds
    num_moves = Column(Integer, nullable=False)  # Move count
    scramble = Column(String(500), nullable=True)  # Initial scramble
    solution = Column(String(1000), nullable=False)  # Move sequence
    solver_used = Column(String(50), default="manual", nullable=False)  # manual, kociemba, etc.
    confidence = Column(Float, default=1.0)  # Solver confidence in solution (0.0-1.0)
    is_dnf = Column(Boolean, default=False)  # Did Not Finish
    is_dns = Column(Boolean, default=False)  # Did Not Start
    notes = Column(String(500), nullable=True)  # User notes
    metadata = Column(JSON, nullable=True)  # Additional data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    profile = relationship("Profile", back_populates="solve_records")
    coaching_records = relationship("CoachingRecord", back_populates="solve_record")

    def __repr__(self):
        return f"<SolveRecord(id={self.id}, time={self.time_ms}ms)>"


class ScanSession(Base):
    """Cube scanning session tracking."""
    __tablename__ = "scan_sessions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    session_key = Column(String(36), unique=True, nullable=False)  # UUID for WebSocket session
    status = Column(String(20), default="active", nullable=False)  # active, completed, cancelled
    detected_cube_state = Column(JSON, nullable=True)  # Detected cube state JSON
    confidence = Column(Float, default=0.0)  # Detection confidence
    num_frames_processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship("Profile", back_populates="scan_sessions")

    def __repr__(self):
        return f"<ScanSession(id={self.id}, status={self.status})>"


class CoachingRecord(Base):
    """Coaching interaction history."""
    __tablename__ = "coaching_records"

    id = Column(Integer, primary_key=True, index=True)
    solve_record_id = Column(Integer, ForeignKey("solve_records.id"), nullable=False, index=True)
    focus_area = Column(String(50), default="overall", nullable=False)  # cross, f2l, oll, pll, overall
    explanation = Column(String(2000), nullable=False)
    key_points = Column(JSON, nullable=False)  # List of key points
    suggested_algorithms = Column(JSON, nullable=False)  # List of algorithms
    difficulty_level = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    user_rating = Column(Integer, nullable=True)  # 1-5 star rating if user provides feedback
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    solve_record = relationship("SolveRecord", back_populates="coaching_records")

    def __repr__(self):
        return f"<CoachingRecord(id={self.id}, focus={self.focus_area})>"
