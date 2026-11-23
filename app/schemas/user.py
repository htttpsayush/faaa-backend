from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    name: str
    weight_kg: Optional[float] = 70.0
    height_cm: Optional[float] = 175.0
    calorie_target: Optional[int] = 2000
    diet_preference: Optional[str] = "any"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    weight_kg: Optional[float] = 70.0
    height_cm: Optional[float] = 175.0
    calorie_target: Optional[int] = 2000
    diet_preference: Optional[str] = "any"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    calorie_target: Optional[int] = None
    diet_preference: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
