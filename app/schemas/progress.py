from typing import List, Optional
from pydantic import BaseModel
from app.schemas.workout import WorkoutResponse

class DailyCalorie(BaseModel):
    day: str
    date: str
    calories: float
    is_today: bool = False

class ProgressSummaryResponse(BaseModel):
    pulse_score: int
    bmi: float
    bmi_category: str
    today_calories: float
    target_calories: int
    remaining_calories: float
    calorie_progress_pct: int
    completed_workouts_this_week: int
    weekly_workouts_target: int = 5
    seven_day_trend: str
    weekly_calories: List[DailyCalorie]
    today_workout: Optional[WorkoutResponse] = None
