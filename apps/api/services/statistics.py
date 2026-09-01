"""
Statistics calculations and aggregation for solver performance.
Calculates Ao5, Ao12, Ao100, best, worst, and trends.
"""

import logging
from statistics import mean
from sqlalchemy.orm import Session

from ..db.models import SolveRecord, Profile
from ..models import StatisticsModel
from ..errors import NotFoundError

logger = logging.getLogger(__name__)


class StatisticsService:
    """Service for calculating cubing statistics."""
    
    @staticmethod
    def get_statistics(db: Session, profile_id: int) -> StatisticsModel:
        """
        Calculate comprehensive statistics for a profile.
        
        Includes:
        - Total solves count
        - Best time
        - Worst time
        - Average of last 5 (Ao5)
        - Average of last 12 (Ao12)
        - Average of last 100 (Ao100)
        - Overall average
        - Standard deviation (DNAs)
        
        Args:
            db: Database session
            profile_id: Profile ID
            
        Returns:
            StatisticsModel with calculated stats
        """
        # Verify profile exists
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise NotFoundError(f"Profile {profile_id} not found")
        
        # Get all valid solves (exclude DNF/DNS), ordered by most recent first
        solves = (
            db.query(SolveRecord)
            .filter(SolveRecord.profile_id == profile_id)
            .filter(SolveRecord.is_dnf == False)
            .filter(SolveRecord.is_dns == False)
            .order_by(SolveRecord.created_at.desc())
            .all()
        )
        
        if not solves:
            # Return empty statistics if no solves
            return StatisticsModel(
                profile_id=profile_id,
                total_solves=0,
                best_time_ms=None,
                worst_time_ms=None,
                average_ao5_ms=None,
                average_ao12_ms=None,
                average_ao100_ms=None,
                average_overall_ms=None,
            )
        
        times = [solve.time_ms for solve in solves]
        
        # Calculate statistics
        total_solves = len(solves)
        best_time = min(times)
        worst_time = max(times)
        
        # Ao5 - Average of 5 (best of last 5 averages)
        ao5 = None
        if total_solves >= 5:
            ao5 = mean(times[:5])
        
        # Ao12 - Average of 12
        ao12 = None
        if total_solves >= 12:
            ao12 = mean(times[:12])
        
        # Ao100 - Average of 100
        ao100 = None
        if total_solves >= 100:
            ao100 = mean(times[:100])
        
        # Overall average
        overall_avg = mean(times)
        
        logger.info(
            f"Calculated statistics for profile {profile_id}",
            extra={
                "total_solves": total_solves,
                "ao5": ao5,
                "ao12": ao12,
                "ao100": ao100,
            },
        )
        
        return StatisticsModel(
            profile_id=profile_id,
            total_solves=total_solves,
            best_time_ms=best_time,
            worst_time_ms=worst_time,
            average_ao5_ms=ao5,
            average_ao12_ms=ao12,
            average_ao100_ms=ao100,
            average_overall_ms=overall_avg,
        )
    
    @staticmethod
    def get_recent_improvement(db: Session, profile_id: int) -> dict:
        """
        Calculate recent improvement trend.
        
        Compares Ao5 of most recent solves with Ao5 from 50 solves ago.
        
        Args:
            db: Database session
            profile_id: Profile ID
            
        Returns:
            {
                "recent_ao5": float,
                "previous_ao5": float,
                "improvement_ms": float,
                "improvement_percent": float,
                "trend": "improving" | "stable" | "declining"
            }
        """
        solves = (
            db.query(SolveRecord)
            .filter(SolveRecord.profile_id == profile_id)
            .filter(SolveRecord.is_dnf == False)
            .filter(SolveRecord.is_dns == False)
            .order_by(SolveRecord.created_at.desc())
            .all()
        )
        
        if len(solves) < 10:
            # Not enough data for trend analysis
            return {
                "recent_ao5": None,
                "previous_ao5": None,
                "improvement_ms": None,
                "improvement_percent": None,
                "trend": "insufficient_data",
            }
        
        # Recent Ao5 (first 5 solves)
        recent_times = [solve.time_ms for solve in solves[:5]]
        recent_ao5 = mean(recent_times)
        
        # Previous Ao5 (5 solves around position 50)
        if len(solves) >= 55:
            previous_times = [solve.time_ms for solve in solves[50:55]]
            previous_ao5 = mean(previous_times)
        else:
            # Use earlier average if less than 55 solves
            previous_times = [solve.time_ms for solve in solves[-5:]]
            previous_ao5 = mean(previous_times)
        
        improvement_ms = previous_ao5 - recent_ao5
        improvement_percent = (improvement_ms / previous_ao5) * 100 if previous_ao5 > 0 else 0
        
        # Determine trend
        if improvement_ms > 100:  # > 100ms improvement
            trend = "improving"
        elif improvement_ms < -100:  # > 100ms decline
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "recent_ao5": recent_ao5,
            "previous_ao5": previous_ao5,
            "improvement_ms": improvement_ms,
            "improvement_percent": improvement_percent,
            "trend": trend,
        }
    
    @staticmethod
    def get_milestone_stats(db: Session, profile_id: int) -> dict:
        """
        Get milestone statistics (personal records, targets).
        
        Tracks:
        - All-time best solve
        - Best daily time
        - Best weekly average
        - Target times (sub-30, sub-20, sub-10)
        
        Args:
            db: Database session
            profile_id: Profile ID
            
        Returns:
            Dictionary with milestone information
        """
        solves = (
            db.query(SolveRecord)
            .filter(SolveRecord.profile_id == profile_id)
            .filter(SolveRecord.is_dnf == False)
            .filter(SolveRecord.is_dns == False)
            .order_by(SolveRecord.time_ms)
            .all()
        )
        
        if not solves:
            return {
                "pb_single": None,
                "pb_time_str": "No solves",
                "sub_30_achieved": False,
                "sub_20_achieved": False,
                "sub_10_achieved": False,
            }
        
        best_time = solves[0].time_ms
        best_time_str = StatisticsService._format_time(best_time)
        
        return {
            "pb_single": best_time,
            "pb_time_str": best_time_str,
            "sub_30_achieved": best_time < 30000,
            "sub_20_achieved": best_time < 20000,
            "sub_10_achieved": best_time < 10000,
        }
    
    @staticmethod
    def _format_time(time_ms: int) -> str:
        """Format time in milliseconds to readable format (MM:SS.ms)."""
        total_seconds = time_ms / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}:{seconds:06.3f}"
        else:
            return f"{seconds:5.3f}"


def format_solve_time(time_ms: int) -> str:
    """Format solve time as MM:SS.ms or SS.ms."""
    return StatisticsService._format_time(time_ms)
