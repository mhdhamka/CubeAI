"""Training-attempt persistence endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import TrainingAttemptModel
from ..services.training import TrainingService, training_attempt_to_model

router = APIRouter(prefix="/api", tags=["training"])


@router.post("/training", response_model=TrainingAttemptModel, status_code=status.HTTP_201_CREATED)
async def create_training_attempt(
    attempt: TrainingAttemptModel,
    db: Session = Depends(get_db),
) -> TrainingAttemptModel:
    return training_attempt_to_model(TrainingService.record_attempt(db, attempt))


@router.get("/profiles/{profile_id}/training", response_model=list[TrainingAttemptModel])
async def get_training_attempts(
    profile_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[TrainingAttemptModel]:
    return [
        training_attempt_to_model(record)
        for record in TrainingService.get_attempts(db, profile_id, limit)
    ]