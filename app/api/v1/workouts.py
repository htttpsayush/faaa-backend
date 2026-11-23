from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.workout import (
    WorkoutCreate,
    WorkoutGenerateRequest,
    WorkoutGenerateResponse,
    WorkoutResponse,
    WorkoutUpdate
)
from app.services.workout_service import workout_service
from app.services.workout_ai_service import workout_ai_service

router = APIRouter(prefix="/workouts", tags=["Workouts"])

@router.get("/", response_model=List[WorkoutResponse])
def list_workouts(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return workout_service.list_workouts(db, current_user.id, category=category)

@router.post("/", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(
    workout_in: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return workout_service.create_workout(db, current_user.id, workout_in)

@router.post("/generate", response_model=WorkoutGenerateResponse)
def generate_workout(
    req: WorkoutGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates a tailored workout session with exercises and safety rules."""
    return workout_ai_service.generate_workout(db, current_user, req)

@router.get("/{id}", response_model=WorkoutResponse)
def get_workout(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return WorkoutResponse.model_validate(workout_service.get_workout(db, id, current_user.id))

@router.put("/{id}", response_model=WorkoutResponse)
def update_workout(
    id: int,
    workout_in: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return workout_service.update_workout(db, id, current_user.id, workout_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workout_service.delete_workout(db, id, current_user.id)
    return None

@router.patch("/{id}/complete", response_model=WorkoutResponse)
def toggle_complete(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return workout_service.toggle_complete(db, id, current_user.id)
