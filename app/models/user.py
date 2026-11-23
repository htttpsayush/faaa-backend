from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    weight_kg = Column(Float, nullable=True, default=70.0)
    height_cm = Column(Float, nullable=True, default=175.0)
    calorie_target = Column(Integer, nullable=True, default=2000)
    diet_preference = Column(String(20), nullable=False, default="any", server_default="any")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")
