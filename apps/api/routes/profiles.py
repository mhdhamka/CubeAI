"""
Profile management endpoints.
CRUD operations for user profiles.
"""

import logging
from fastapi import APIRouter, Depends, status

from ..db import get_db, Profile
from ..models import ProfileModel
from ..services.profile import ProfileService, profile_to_model
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get(
    "/{profile_id}",
    response_model=ProfileModel,
    status_code=status.HTTP_200_OK,
    summary="Get a profile",
)
async def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
) -> ProfileModel:
    """
    Get a profile by ID.
    
    **Response:**
    ```json
    {
        "id": 1,
        "user_id": 1,
        "name": "My 3x3 Profile",
        "cube_size": 3,
        "solving_method": "cfop",
        "preferred_focus": "overall",
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00"
    }
    ```
    """
    profile = ProfileService.get_profile(db, profile_id)
    return profile_to_model(profile)


@router.post(
    "",
    response_model=ProfileModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new profile",
)
async def create_profile(
    profile_data: ProfileModel,
    db: Session = Depends(get_db),
) -> ProfileModel:
    """
    Create a new cubing profile for a user.
    
    **Request:**
    ```json
    {
        "user_id": 1,
        "name": "My 3x3 Profile",
        "cube_size": 3,
        "solving_method": "cfop",
        "preferred_focus": "f2l"
    }
    ```
    
    **Response:** (201 Created)
    ```json
    {
        "id": 1,
        "user_id": 1,
        "name": "My 3x3 Profile",
        "cube_size": 3,
        "solving_method": "cfop",
        "preferred_focus": "f2l",
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00"
    }
    ```
    
    **Cube Sizes:**
    - 2: 2x2 Pocket Cube
    - 3: 3x3 Rubik's Cube (default)
    - 4: 4x4 Revenge Cube
    - 5: 5x5 Professor Cube
    - 6+: Other sizes
    
    **Solving Methods:**
    - cfop: Fridrich method (most popular)
    - roux: Roux method
    - petrus: Petrus method
    - zz: ZZ method
    
    **Preferred Focus:**
    - cross: Focus on cross technique
    - f2l: Focus on First Two Layers
    - oll: Focus on Orient Last Layer
    - pll: Focus on Permute Last Layer
    - overall: General overall improvement
    """
    profile = ProfileService.create_profile(
        db,
        profile_data.dict(exclude_unset=True),
    )
    return profile_to_model(profile)


@router.put(
    "/{profile_id}",
    response_model=ProfileModel,
    status_code=status.HTTP_200_OK,
    summary="Update a profile",
)
async def update_profile(
    profile_id: int,
    profile_data: ProfileModel,
    db: Session = Depends(get_db),
) -> ProfileModel:
    """
    Update an existing profile.
    """
    profile = ProfileService.update_profile(
        db,
        profile_id,
        profile_data.dict(exclude_unset=True),
    )
    return profile_to_model(profile)


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a profile",
)
async def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a profile and all associated solve records.
    
    **WARNING:** This is irreversible!
    """
    ProfileService.delete_profile(db, profile_id)
