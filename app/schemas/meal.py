from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class MealBase(BaseModel):
    name: str
    calories: float
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fats_g: float = 0.0
    portion_size: Optional[str] = "1 serving"

class MealCreate(MealBase):
    pass

class MealResponse(MealBase):
    id: int
    user_id: int
    logged_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class NutritionTodayResponse(BaseModel):
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float
    target_calories: int
    remaining_calories: float

# Schemas for Photo Meal Analysis
class AnalyzedFoodItem(BaseModel):
    name: str
    estimated_grams: Optional[float] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fats_g: Optional[float] = None
    confidence: float = 1.0  # 0.0 to 1.0
    needs_input: bool = False
    reason: Optional[str] = None

class PhotoAnalysisResponse(BaseModel):
    items: List[AnalyzedFoodItem]
    is_estimate: bool = True
    message: Optional[str] = "Values are estimated. Please review before logging."

# Schemas for Diet Suggestions
class FoodSuggestion(BaseModel):
    food_name: str
    serving: str
    nutrient_amount: str

class NutrientShortfall(BaseModel):
    nutrient: str
    shortfall_amount: float
    unit: str
    target: float
    consumed: float
    suggestions: List[FoodSuggestion] = []

class DietSuggestionsResponse(BaseModel):
    has_shortfall: bool
    diet_preference: str
    remaining_calories: float
    shortfalls: List[NutrientShortfall] = []
    message: Optional[str] = None
