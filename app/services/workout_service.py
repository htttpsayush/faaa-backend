from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.workout import Workout
from app.repositories.workout_repo import workout_repo
from app.schemas.workout import WorkoutCreate, WorkoutUpdate, WorkoutResponse

class WorkoutService:
    @staticmethod
    def get_workout(db: Session, workout_id: int, user_id: int) -> Workout:
        workout = workout_repo.get_by_id(db, workout_id, user_id)
        if not workout:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
        return workout

    @staticmethod
    def list_workouts(db: Session, user_id: int, category: Optional[str] = None) -> List[WorkoutResponse]:
        items = workout_repo.list_by_user(db, user_id, category=category)
        return [WorkoutResponse.model_validate(w) for w in items]

    @staticmethod
    def create_workout(db: Session, user_id: int, workout_in: WorkoutCreate) -> WorkoutResponse:
        workout = workout_repo.create(db, user_id, workout_in)
        return WorkoutResponse.model_validate(workout)

    @staticmethod
    def update_workout(db: Session, workout_id: int, user_id: int, workout_in: WorkoutUpdate) -> WorkoutResponse:
        workout = WorkoutService.get_workout(db, workout_id, user_id)
        updated = workout_repo.update(db, workout, workout_in)
        return WorkoutResponse.model_validate(updated)

    @staticmethod
    def delete_workout(db: Session, workout_id: int, user_id: int) -> None:
        workout = WorkoutService.get_workout(db, workout_id, user_id)
        workout_repo.delete(db, workout)

    @staticmethod
    def toggle_complete(db: Session, workout_id: int, user_id: int) -> WorkoutResponse:
        workout = WorkoutService.get_workout(db, workout_id, user_id)
        new_status = not workout.is_completed
        updated = workout_repo.update(db, workout, WorkoutUpdate(is_completed=new_status))
        return WorkoutResponse.model_validate(updated)

workout_service = WorkoutService()
