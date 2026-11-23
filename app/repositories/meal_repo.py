from datetime import datetime, date, time
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.meal import Meal
from app.schemas.meal import MealCreate

class MealRepository:
    @staticmethod
    def get_by_id(db: Session, meal_id: int, user_id: int) -> Optional[Meal]:
        return db.query(Meal).filter(Meal.id == meal_id, Meal.user_id == user_id).first()

    @staticmethod
    def list_by_user_today(db: Session, user_id: int, target_date: Optional[date] = None) -> List[Meal]:
        d = target_date or date.today()
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
        return db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.logged_at >= start,
            Meal.logged_at <= end
        ).order_by(Meal.logged_at.desc()).all()

    @staticmethod
    def list_all_by_user(db: Session, user_id: int) -> List[Meal]:
        return db.query(Meal).filter(Meal.user_id == user_id).order_by(Meal.logged_at.desc()).all()

    @staticmethod
    def create(db: Session, user_id: int, obj_in: MealCreate) -> Meal:
        db_obj = Meal(
            user_id=user_id,
            name=obj_in.name,
            calories=obj_in.calories,
            protein_g=obj_in.protein_g,
            carbs_g=obj_in.carbs_g,
            fats_g=obj_in.fats_g,
            portion_size=obj_in.portion_size or "1 serving"
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: Meal) -> None:
        db.delete(db_obj)
        db.commit()

    @staticmethod
    def get_daily_totals(db: Session, user_id: int, target_date: Optional[date] = None) -> dict:
        d = target_date or date.today()
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
        res = db.query(
            func.coalesce(func.sum(Meal.calories), 0.0).label("cals"),
            func.coalesce(func.sum(Meal.protein_g), 0.0).label("protein"),
            func.coalesce(func.sum(Meal.carbs_g), 0.0).label("carbs"),
            func.coalesce(func.sum(Meal.fats_g), 0.0).label("fats")
        ).filter(
            Meal.user_id == user_id,
            Meal.logged_at >= start,
            Meal.logged_at <= end
        ).first()

        return {
            "calories": float(res.cals) if res else 0.0,
            "protein": float(res.protein) if res else 0.0,
            "carbs": float(res.carbs) if res else 0.0,
            "fats": float(res.fats) if res else 0.0,
        }

meal_repo = MealRepository()
