import json
from datetime import date
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from pydantic import ValidationError
from groq import Groq
from app.core.config import settings
from app.models.user import User
from app.repositories.meal_repo import meal_repo
from app.schemas.meal import (
    DietSuggestionsResponse,
    FoodSuggestion,
    NutrientShortfall
)

DIET_PROMPT_TEMPLATE = """You are an expert sports nutrition dietitian.
The athlete has the following nutritional shortfalls today:
Dietary preference: {preference}
Remaining calorie allowance: {remaining_calories} kcal
Shortfalls:
{shortfall_summary}

Provide practical, whole-food suggestions that strictly respect the athlete's dietary preference ({preference}).
Return a STRICT JSON object in this exact format:
{{
  "suggestions_by_nutrient": {{
    "Protein": [
      {{
        "food_name": "Greek Yogurt (0% fat)",
        "serving": "1 cup (200g)",
        "nutrient_amount": "20g protein"
      }}
    ]
  }}
}}

Rules:
1. Provide up to 3 practical, accessible food suggestions per short nutrient.
2. Must strictly honor dietary preference:
   - "veg": strictly vegetarian (dairy/eggs allowed unless vegan is specified, no meat/fish).
   - "non_veg": can include lean meats, fish, poultry, eggs, dairy, or plant proteins.
   - "any": any high-quality nutritious source.
3. Keep serving sizes realistic and common.
4. Return ONLY the valid JSON object.
"""

class DietSuggestionService:
    @staticmethod
    def calculate_shortfalls(user: User, consumed_totals: dict) -> List[NutrientShortfall]:
        """
        Pure function: calculates targets and checks if consumed nutrients
        fall more than 10% below budget.
        """
        cfg = settings.DIET_TARGETS_CONFIG
        cal_target = float(user.calorie_target or 2000)
        weight_kg = float(user.weight_kg or 70.0)

        # 1. Macro targets according to config
        protein_target = round(cfg["PROTEIN_GRAMS_PER_KG"] * weight_kg, 1)
        fats_target = round((cfg["FATS_CALORIE_PERCENT"] * cal_target) / cfg["CALORIES_PER_FAT_GRAM"], 1)
        carb_cals = max(0.0, cal_target - (protein_target * cfg["CALORIES_PER_PROTEIN_GRAM"]) - (fats_target * cfg["CALORIES_PER_FAT_GRAM"]))
        carbs_target = round(carb_cals / cfg["CALORIES_PER_CARB_GRAM"], 1)

        consumed_protein = float(consumed_totals.get("protein", 0.0))
        consumed_carbs = float(consumed_totals.get("carbs", 0.0))
        consumed_fats = float(consumed_totals.get("fats", 0.0))

        threshold_pct = cfg["SHORTFALL_THRESHOLD_PCT"]
        shortfalls: List[NutrientShortfall] = []

        # Check Protein
        if consumed_protein < (protein_target * (1.0 - threshold_pct)):
            shortfalls.append(NutrientShortfall(
                nutrient="Protein",
                shortfall_amount=round(protein_target - consumed_protein, 1),
                unit="g",
                target=protein_target,
                consumed=round(consumed_protein, 1),
                suggestions=[]
            ))

        # Check Carbohydrates
        if consumed_carbs < (carbs_target * (1.0 - threshold_pct)):
            shortfalls.append(NutrientShortfall(
                nutrient="Carbohydrates",
                shortfall_amount=round(carbs_target - consumed_carbs, 1),
                unit="g",
                target=carbs_target,
                consumed=round(consumed_carbs, 1),
                suggestions=[]
            ))

        # Check Fats
        if consumed_fats < (fats_target * (1.0 - threshold_pct)):
            shortfalls.append(NutrientShortfall(
                nutrient="Fats",
                shortfall_amount=round(fats_target - consumed_fats, 1),
                unit="g",
                target=fats_target,
                consumed=round(consumed_fats, 1),
                suggestions=[]
            ))

        return shortfalls

    @staticmethod
    def get_suggestions(db: Session, user: User) -> DietSuggestionsResponse:
        today = date.today()
        totals = meal_repo.get_daily_totals(db, user.id, today)
        cal_target = float(user.calorie_target or 2000)
        consumed_cals = float(totals.get("calories", 0.0))
        remaining_cals = max(0.0, cal_target - consumed_cals)
        preference = getattr(user, "diet_preference", "any") or "any"

        # Empty state 1: No meals logged yet today
        if consumed_cals == 0:
            return DietSuggestionsResponse(
                has_shortfall=False,
                diet_preference=preference,
                remaining_calories=remaining_cals,
                shortfalls=[],
                message="Log a meal to get suggestions"
            )

        shortfalls = DietSuggestionService.calculate_shortfalls(user, totals)

        # Empty state 2: All nutrients on track (nothing short)
        if not shortfalls:
            return DietSuggestionsResponse(
                has_shortfall=False,
                diet_preference=preference,
                remaining_calories=remaining_cals,
                shortfalls=[],
                message="You're on track today"
            )

        # If Groq API key is not configured, return shortfall figures without AI suggestions
        if not settings.GROQ_API_KEY:
            return DietSuggestionsResponse(
                has_shortfall=True,
                diet_preference=preference,
                remaining_calories=remaining_cals,
                shortfalls=shortfalls,
                message="Nutrient shortfalls calculated. Set GROQ_API_KEY to enable AI food suggestions."
            )

        # Prepare prompt for Groq text model
        shortfall_lines = [
            f"- {s.nutrient}: {s.shortfall_amount} {s.unit} short (consumed: {s.consumed}/{s.target} {s.unit})"
            for s in shortfalls
        ]
        prompt = DIET_PROMPT_TEMPLATE.format(
            preference=preference,
            remaining_calories=round(remaining_cals),
            shortfall_summary="\n".join(shortfall_lines)
        )

        try:
            client = Groq(api_key=settings.GROQ_API_KEY, timeout=20.0)
            for attempt in range(2):
                try:
                    completion = client.chat.completions.create(
                        model=settings.GROQ_TEXT_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                        temperature=0.3,
                    )
                    content = completion.choices[0].message.content or "{}"
                    data = json.loads(content)
                    suggestions_map = data.get("suggestions_by_nutrient", {})

                    for sf in shortfalls:
                        raw_list = suggestions_map.get(sf.nutrient, [])
                        sf.suggestions = [
                            FoodSuggestion(
                                food_name=item.get("food_name", ""),
                                serving=item.get("serving", "1 serving"),
                                nutrient_amount=item.get("nutrient_amount", "")
                            )
                            for item in raw_list[:3]
                            if isinstance(item, dict) and item.get("food_name")
                        ]
                    break
                except (json.JSONDecodeError, ValidationError):
                    if attempt == 1:
                        # Fallback to returning shortfalls without food list
                        pass
        except Exception:
            # Non-blocking failure: keep shortfalls available
            pass

        return DietSuggestionsResponse(
            has_shortfall=True,
            diet_preference=preference,
            remaining_calories=remaining_cals,
            shortfalls=shortfalls,
            message=None
        )

diet_suggestion_service = DietSuggestionService()
