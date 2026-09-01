"""
CRUD operations for user profiles.
"""

import logging
from sqlalchemy.orm import Session

from ..db.models import User, Profile
from ..models import ProfileModel
from ..errors import NotFoundError

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles."""
    
    @staticmethod
    def create_profile(db: Session, profile_data: dict) -> Profile:
        """
        Create a new profile for a user.
        
        Args:
            db: Database session
            profile_data: Profile data with user_id, name, cube_size, etc.
            
        Returns:
            Created Profile instance
        """
        db_profile = Profile(**profile_data)
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        logger.info(f"Created profile: {db_profile.id}")
        return db_profile
    
    @staticmethod
    def get_profile(db: Session, profile_id: int) -> Profile:
        """
        Get a profile by ID.
        
        Args:
            db: Database session
            profile_id: Profile ID
            
        Returns:
            Profile instance
            
        Raises:
            NotFoundError: If profile not found
        """
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise NotFoundError(f"Profile {profile_id} not found")
        return profile
    
    @staticmethod
    def get_user_profiles(db: Session, user_id: int) -> list[Profile]:
        """
        Get all profiles for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of Profile instances
        """
        return db.query(Profile).filter(Profile.user_id == user_id).all()
    
    @staticmethod
    def update_profile(db: Session, profile_id: int, profile_data: dict) -> Profile:
        """
        Update a profile.
        
        Args:
            db: Database session
            profile_id: Profile ID
            profile_data: Updated data
            
        Returns:
            Updated Profile instance
        """
        profile = ProfileService.get_profile(db, profile_id)
        
        for key, value in profile_data.items():
            if value is not None:
                setattr(profile, key, value)
        
        db.commit()
        db.refresh(profile)
        logger.info(f"Updated profile: {profile_id}")
        return profile
    
    @staticmethod
    def delete_profile(db: Session, profile_id: int) -> None:
        """
        Delete a profile.
        
        Args:
            db: Database session
            profile_id: Profile ID
        """
        profile = ProfileService.get_profile(db, profile_id)
        db.delete(profile)
        db.commit()
        logger.info(f"Deleted profile: {profile_id}")


def profile_to_model(profile: Profile) -> ProfileModel:
    """Convert SQLAlchemy Profile to Pydantic ProfileModel."""
    return ProfileModel(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        cube_size=profile.cube_size,
        solving_method=profile.solving_method,
        preferred_focus=profile.preferred_focus,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
