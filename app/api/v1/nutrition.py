from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.meal import (
    DietSuggestionsResponse,
    MealCreate,
    MealResponse,
    NutritionTodayResponse,
    PhotoAnalysisResponse
)
from app.repositories.meal_repo import meal_repo
from app.services.food_service import food_service
from app.services.food_vision_service import food_vision_service
from app.services.diet_suggestion_service import diet_suggestion_service

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])

@router.get("/meals", response_model=List[MealResponse])
def list_meals(
    date_filter: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if date_filter:
        items = meal_repo.list_by_user_today(db, current_user.id, date_filter)
    else:
        items = meal_repo.list_all_by_user(db, current_user.id)
    return [MealResponse.model_validate(m) for m in items]

@router.post("/meals", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def create_meal(
    meal_in: MealCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sanitized = food_service.process_meal_entry(meal_in)
    meal = meal_repo.create(db, current_user.id, sanitized)
    return MealResponse.model_validate(meal)

@router.delete("/meals/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meal = meal_repo.get_by_id(db, id, current_user.id)
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    meal_repo.delete(db, meal)
    return None

@router.get("/today", response_model=NutritionTodayResponse)
def get_today_nutrition(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    totals = meal_repo.get_daily_totals(db, current_user.id, date.today())
    target = current_user.calorie_target or 2000
    remaining = max(0.0, target - totals["calories"])
    return NutritionTodayResponse(
        total_calories=round(totals["calories"], 1),
        total_protein=round(totals["protein"], 1),
        total_carbs=round(totals["carbs"], 1),
        total_fats=round(totals["fats"], 1),
        target_calories=target,
        remaining_calories=round(remaining, 1)
    )

@router.post("/analyze-photo", response_model=PhotoAnalysisResponse)
async def analyze_meal_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Analyzes a food photo using Groq vision inference without saving the image."""
    return await food_vision_service.analyze_photo(file)

@router.get("/suggestions", response_model=DietSuggestionsResponse)
def get_diet_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculates macro shortfalls and provides targeted food suggestions."""
    return diet_suggestion_service.get_suggestions(db, current_user)
