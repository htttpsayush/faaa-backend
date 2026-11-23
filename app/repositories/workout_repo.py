from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.workout import Workout
from app.schemas.workout import WorkoutCreate, WorkoutUpdate

class WorkoutRepository:
    @staticmethod
    def get_by_id(db: Session, workout_id: int, user_id: int) -> Optional[Workout]:
        return db.query(Workout).filter(Workout.id == workout_id, Workout.user_id == user_id).first()

    @staticmethod
    def list_by_user(db: Session, user_id: int, category: Optional[str] = None) -> List[Workout]:
        query = db.query(Workout).filter(Workout.user_id == user_id)
        if category and category.lower() != "all":
            query = query.filter(Workout.category == category.lower())
        return query.order_by(Workout.workout_date.desc(), Workout.id.desc()).all()

    @staticmethod
    def list_recent_by_category(db: Session, user_id: int, category: str, limit: int = 5) -> List[Workout]:
        return db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.category == category.lower()
        ).order_by(Workout.workout_date.desc(), Workout.id.desc()).limit(limit).all()

    @staticmethod
    def create(db: Session, user_id: int, obj_in: WorkoutCreate) -> Workout:
        db_obj = Workout(
            user_id=user_id,
            name=obj_in.name,
            category=obj_in.category or "gym",
            duration_min=obj_in.duration_min,
            volume_kg=obj_in.volume_kg,
            avg_hr=obj_in.avg_hr,
            is_completed=obj_in.is_completed,
            exercises=obj_in.exercises,
            workout_date=obj_in.workout_date or date.today()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(db: Session, db_obj: Workout, obj_in: WorkoutUpdate) -> Workout:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: Workout) -> None:
        db.delete(db_obj)
        db.commit()

workout_repo = WorkoutRepository()
