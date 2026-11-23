from datetime import date, timedelta
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.workout import Workout
from app.repositories.meal_repo import meal_repo
from app.schemas.progress import ProgressSummaryResponse, DailyCalorie
from app.schemas.workout import WorkoutResponse

class ProgressService:
    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> Tuple[float, str]:
        """Calculates BMI and returns (bmi_value, category_string)."""
        if not weight_kg or not height_cm or height_cm <= 0:
            return 22.0, "Normal"
        height_m = height_cm / 100.0
        bmi_val = round(weight_kg / (height_m * height_m), 1)
        if bmi_val < 18.5:
            cat = "Underweight"
        elif bmi_val <= 24.9:
            cat = "Normal"
        elif bmi_val <= 29.9:
            cat = "Overweight"
        else:
            cat = "Obese"
        return bmi_val, cat

    @staticmethod
    def get_summary(db: Session, user: User) -> ProgressSummaryResponse:
        """Computes athlete PulseScore, BMI, 7-day trend, and weekly metrics."""
        today = date.today()
        user_id = user.id

        # 1. Calories consumed today vs target
        today_totals = meal_repo.get_daily_totals(db, user_id, today)
        today_cals = today_totals["calories"]
        target_cals = user.calorie_target or 2000
        remaining_cals = max(0.0, target_cals - today_cals)
        pct = min(100, int((today_cals / target_cals) * 100)) if target_cals > 0 else 0

        # 2. Completed workouts this week (Monday to Sunday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        completed_workouts_count = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.is_completed == True,
            Workout.workout_date >= start_of_week,
            Workout.workout_date <= end_of_week
        ).count()

        # 3. PulseScore (0-100 composite):
        # 50 points for caloric adherence + 50 points for weekly workout consistency (5 target)
        if target_cals > 0:
            cal_diff = abs(today_cals - target_cals)
            cal_score = max(0.0, 50.0 - (cal_diff / float(target_cals)) * 50.0)
        else:
            cal_score = 0.0

        workout_score = min(50.0, (completed_workouts_count / 5.0) * 50.0)
        pulse_score = max(0, min(100, int(round(cal_score + workout_score))))

        # 4. Body Mass Index
        bmi_val, bmi_cat = ProgressService.calculate_bmi(user.weight_kg or 70.0, user.height_cm or 175.0)

        # 5. Last 7 calendar days caloric history
        weekly_calories: List[DailyCalorie] = []
        cals_sum_7days = 0.0
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            day_str = d.strftime("%a").upper()
            date_str = d.strftime("%Y-%m-%d")
            day_total = meal_repo.get_daily_totals(db, user_id, d)["calories"]
            cals_sum_7days += day_total
            weekly_calories.append(
                DailyCalorie(
                    day=day_str,
                    date=date_str,
                    calories=day_total,
                    is_today=(d == today)
                )
            )

        # 6. Trend categorization
        avg_7days = cals_sum_7days / 7.0
        if avg_7days == 0:
            trend = "Fresh Start"
        elif abs(avg_7days - target_cals) <= 200:
            trend = "On Track"
        elif avg_7days > target_cals:
            trend = "Calorie Surplus"
        else:
            trend = "Calorie Deficit"

        # 7. Today's latest workout (if any)
        today_workout_obj = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.workout_date == today
        ).order_by(Workout.id.desc()).first()

        today_workout_resp = WorkoutResponse.model_validate(today_workout_obj) if today_workout_obj else None

        return ProgressSummaryResponse(
            pulse_score=pulse_score,
            bmi=bmi_val,
            bmi_category=bmi_cat,
            today_calories=today_cals,
            target_calories=target_cals,
            remaining_calories=remaining_cals,
            calorie_progress_pct=pct,
            completed_workouts_this_week=completed_workouts_count,
            weekly_workouts_target=5,
            seven_day_trend=trend,
            weekly_calories=weekly_calories,
            today_workout=today_workout_resp
        )

progress_service = ProgressService()
