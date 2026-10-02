"""Persistence operations for algorithm training attempts."""

from sqlalchemy.orm import Session

from ..db.models import Profile, TrainingAttempt
from ..errors import NotFoundError
from ..models import TrainingAttemptModel


class TrainingService:
    @staticmethod
    def record_attempt(db: Session, attempt: TrainingAttemptModel) -> TrainingAttempt:
        if db.query(Profile).filter(Profile.id == attempt.profile_id).first() is None:
            raise NotFoundError("Profile", attempt.profile_id)
        record = TrainingAttempt(
            profile_id=attempt.profile_id,
            algorithm=attempt.algorithm,
            recognition_time_ms=attempt.recognition_time_ms,
            execution_time_ms=attempt.execution_time_ms,
            was_correct=attempt.was_correct,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_attempts(db: Session, profile_id: int, limit: int = 100) -> list[TrainingAttempt]:
        if db.query(Profile).filter(Profile.id == profile_id).first() is None:
            raise NotFoundError("Profile", profile_id)
        return (
            db.query(TrainingAttempt)
            .filter(TrainingAttempt.profile_id == profile_id)
            .order_by(TrainingAttempt.created_at.desc())
            .limit(limit)
            .all()
        )


def training_attempt_to_model(record: TrainingAttempt) -> TrainingAttemptModel:
    return TrainingAttemptModel(
        id=record.id,
        profile_id=record.profile_id,
        algorithm=record.algorithm,
        recognition_time_ms=record.recognition_time_ms,
        execution_time_ms=record.execution_time_ms,
        was_correct=record.was_correct,
        created_at=record.created_at,
    )