"""
Statistics endpoints for performance tracking and analysis.
Provides Ao5, Ao12, Ao100, personal records, and trend analysis.
"""

import logging
from fastapi import APIRouter, Depends, status

from ..db import get_db
from ..models import StatisticsModel
from ..services.statistics import StatisticsService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["statistics"])


@router.get(
    "/profiles/{profile_id}/statistics",
    response_model=StatisticsModel,
    status_code=status.HTTP_200_OK,
    summary="Get profile statistics",
)
async def get_statistics(
    profile_id: int,
    db: Session = Depends(get_db),
) -> StatisticsModel:
    """
    Get comprehensive statistics for a profile.
    
    **Statistics Calculated:**
    - `total_solves`: Total number of valid solves
    - `best_time_ms`: Personal best single solve time
    - `worst_time_ms`: Worst solve time
    - `average_ao5_ms`: Average of last 5 solves
    - `average_ao12_ms`: Average of last 12 solves
    - `average_ao100_ms`: Average of last 100 solves
    - `average_overall_ms`: Overall average of all solves
    
    **Ao Definitions:**
    - **Ao5** (Average of 5): Average of your last 5 solves
      - Most important stat for tracking daily performance
      - Used in most cubing competitions
    
    - **Ao12** (Average of 12): Average of your last 12 solves
      - Longer-term performance indicator
      - Good for tracking week-to-week progress
    
    - **Ao100** (Average of 100): Average of your last 100 solves
      - Long-term progress tracking
      - Shows overall improvement trend
    
    **Note:** DNF (Did Not Finish) and DNS (Did Not Start) solves are excluded.
    
    **Response Example:**
    ```json
    {
        "profile_id": 1,
        "total_solves": 156,
        "best_time_ms": 28450,
        "worst_time_ms": 125340,
        "average_ao5_ms": 32100.5,
        "average_ao12_ms": 33200.75,
        "average_ao100_ms": 35400.25,
        "average_overall_ms": 36500.0
    }
    ```
    
    **Time Format:**
    All times are in milliseconds. Examples:
    - 28450 ms = 28.45 seconds
    - 32100 ms = 32.10 seconds
    - 125340 ms = 2:05.34 (2 minutes 5.34 seconds)
    """
    stats = StatisticsService.get_statistics(db, profile_id)
    return stats


@router.get(
    "/profiles/{profile_id}/statistics/improvement",
    status_code=status.HTTP_200_OK,
    summary="Get improvement trend",
)
async def get_improvement(profile_id: int, db: Session = Depends(get_db)):
    """
    Analyze recent improvement trends.
    
    Compares recent performance with historical performance to identify trends.
    
    **Response:**
    ```json
    {
        "recent_ao5": 32100.5,
        "previous_ao5": 35200.0,
        "improvement_ms": 3099.5,
        "improvement_percent": 8.8,
        "trend": "improving"
    }
    ```
    
    **Trend Values:**
    - `improving`: > 100ms improvement in recent solves
    - `declining`: > 100ms increase in recent solve times
    - `stable`: Within 100ms of previous performance
    - `insufficient_data`: Less than 10 solves recorded
    
    **Use Cases:**
    - Track daily/weekly progress
    - Identify plateaus and breakthroughs
    - Motivate continued practice
    - Plan training adjustments
    """
    improvement = StatisticsService.get_recent_improvement(db, profile_id)
    return improvement


@router.get(
    "/profiles/{profile_id}/statistics/milestones",
    status_code=status.HTTP_200_OK,
    summary="Get milestone achievements",
)
async def get_milestones(profile_id: int, db: Session = Depends(get_db)):
    """
    Get personal record milestones and achievement tracking.
    
    Tracks progress towards common speedcubing targets:
    - Sub-30 (under 30 seconds)
    - Sub-20 (under 20 seconds)
    - Sub-10 (under 10 seconds)
    
    **Response:**
    ```json
    {
        "pb_single": 28450,
        "pb_time_str": "28.450",
        "sub_30_achieved": true,
        "sub_20_achieved": false,
        "sub_10_achieved": false
    }
    ```
    
    **Benchmarks:**
    - **Complete Beginners**: 2-5 minutes
    - **Learning CFOP**: 60-90 seconds
    - **Competent Solver**: 30-60 seconds
    - **Sub-30**: Intermediate milestone
    - **Sub-20**: Advanced milestone
    - **Sub-10**: Expert/Speedcubing level
    - **Sub-5**: Elite speedcuber
    
    **Motivation:**
    This endpoint helps users track their journey and celebrate achievements.
    Each milestone represents significant practice and skill development.
    """
    milestones = StatisticsService.get_milestone_stats(db, profile_id)
    return milestones
