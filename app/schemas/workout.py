from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict

class WorkoutBase(BaseModel):
    name: str
    category: str = "gym"
    duration_min: int = 0
    volume_kg: Optional[float] = None
    avg_hr: Optional[int] = None
    is_completed: bool = False
    exercises: Optional[Any] = None
    workout_date: Optional[date] = None

class WorkoutCreate(WorkoutBase):
    pass

class WorkoutUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    duration_min: Optional[int] = None
    volume_kg: Optional[float] = None
    avg_hr: Optional[int] = None
    is_completed: Optional[bool] = None
    exercises: Optional[Any] = None
    workout_date: Optional[date] = None

class WorkoutResponse(WorkoutBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Schemas for Workout AI Generation
class WorkoutGenerateRequest(BaseModel):
    category: str  # bodyweight, gym, speed, endurance, rehab
    level: Optional[str] = "intermediate"  # beginner, intermediate, advanced
    time_available_min: Optional[int] = 45
    focus: Optional[str] = None  # e.g. full body, upper, sprint, agility
    equipment: Optional[str] = None  # full gym, dumbbells only
    activity: Optional[str] = None  # run, cycle, swim
    target_distance_km: Optional[float] = None
    body_area: Optional[str] = None  # for rehab: shoulder, knee, lower back
    pain_level: Optional[int] = 0  # 0 to 10
    stage: Optional[str] = "early"  # early, mid, late

class GeneratedExerciseItem(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[str] = None
    duration_sec: Optional[int] = None
    rest_sec: Optional[int] = None
    notes: Optional[str] = None

class WorkoutGenerateResponse(BaseModel):
    name: str
    category: str
    estimated_duration_min: int
    exercises: List[GeneratedExerciseItem]
    medical_disclaimer: str = "General guidance only, not medical advice."
    rehab_warning: Optional[str] = None
