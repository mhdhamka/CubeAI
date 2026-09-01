"""
CRUD operations for solve records.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db.models import SolveRecord, Profile
from ..models import SolveRecordModel
from ..errors import NotFoundError

logger = logging.getLogger(__name__)


class SolveService:
    """Service for managing solve records."""
    
    @staticmethod
    def create_solve(db: Session, solve_data: dict) -> SolveRecord:
        """
        Create a new solve record.
        
        Args:
            db: Database session
            solve_data: Solve data with profile_id, time_ms, solution, etc.
            
        Returns:
            Created SolveRecord instance
        """
        # Verify profile exists
        profile = db.query(Profile).filter(Profile.id == solve_data['profile_id']).first()
        if not profile:
            raise NotFoundError(f"Profile {solve_data['profile_id']} not found")
        
        db_solve = SolveRecord(**solve_data)
        db.add(db_solve)
        db.commit()
        db.refresh(db_solve)
        logger.info(f"Created solve record: {db_solve.id} ({db_solve.time_ms}ms)")
        return db_solve
    
    @staticmethod
    def get_solve(db: Session, solve_id: int) -> SolveRecord:
        """
        Get a solve record by ID.
        
        Args:
            db: Database session
            solve_id: Solve record ID
            
        Returns:
            SolveRecord instance
            
        Raises:
            NotFoundError: If solve not found
        """
        solve = db.query(SolveRecord).filter(SolveRecord.id == solve_id).first()
        if not solve:
            raise NotFoundError(f"Solve record {solve_id} not found")
        return solve
    
    @staticmethod
    def get_profile_solves(
        db: Session,
        profile_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SolveRecord]:
        """
        Get all solve records for a profile, ordered by most recent first.
        
        Args:
            db: Database session
            profile_id: Profile ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of SolveRecord instances
        """
        # Verify profile exists
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise NotFoundError(f"Profile {profile_id} not found")
        
        return (
            db.query(SolveRecord)
            .filter(SolveRecord.profile_id == profile_id)
            .filter(SolveRecord.is_dnf == False)  # Exclude DNF by default
            .filter(SolveRecord.is_dns == False)  # Exclude DNS by default
            .order_by(desc(SolveRecord.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    @staticmethod
    def delete_solve(db: Session, solve_id: int) -> None:
        """
        Delete a solve record.
        
        Args:
            db: Database session
            solve_id: Solve record ID
        """
        solve = SolveService.get_solve(db, solve_id)
        db.delete(solve)
        db.commit()
        logger.info(f"Deleted solve record: {solve_id}")
    
    @staticmethod
    def count_profile_solves(db: Session, profile_id: int) -> int:
        """
        Count solve records for a profile (excluding DNF/DNS).
        
        Args:
            db: Database session
            profile_id: Profile ID
            
        Returns:
            Number of solve records
        """
        return (
            db.query(SolveRecord)
            .filter(SolveRecord.profile_id == profile_id)
            .filter(SolveRecord.is_dnf == False)
            .filter(SolveRecord.is_dns == False)
            .count()
        )


def solve_to_model(solve: SolveRecord) -> SolveRecordModel:
    """Convert SQLAlchemy SolveRecord to Pydantic SolveRecordModel."""
    return SolveRecordModel(
        id=solve.id,
        profile_id=solve.profile_id,
        time_ms=solve.time_ms,
        num_moves=solve.num_moves,
        scramble=solve.scramble,
        solution=solve.solution,
        solver_used=solve.solver_used,
        confidence=solve.confidence,
        is_dnf=solve.is_dnf,
        is_dns=solve.is_dns,
        notes=solve.notes,
        created_at=solve.created_at,
    )
