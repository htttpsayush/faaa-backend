from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False, default="gym", server_default="gym", index=True)
    duration_min = Column(Integer, default=0)
    volume_kg = Column(Float, nullable=True, default=0.0)
    avg_hr = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False)
    exercises = Column(JSON, nullable=True)
    workout_date = Column(Date, default=date.today, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="workouts")
