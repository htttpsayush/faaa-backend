from app.schemas.meal import MealCreate

class FoodService:
    @staticmethod
    def process_meal_entry(meal_in: MealCreate) -> MealCreate:
        """Sanitizes meal parameters (clamps negative macros to 0.0, trims name)."""
        cals = max(0.0, float(meal_in.calories))
        protein = max(0.0, float(meal_in.protein_g))
        carbs = max(0.0, float(meal_in.carbs_g))
        fats = max(0.0, float(meal_in.fats_g))
        portion = meal_in.portion_size.strip() if meal_in.portion_size else "1 serving"

        return MealCreate(
            name=meal_in.name.strip(),
            calories=round(cals, 1),
            protein_g=round(protein, 1),
            carbs_g=round(carbs, 1),
            fats_g=round(fats, 1),
            portion_size=portion
        )

food_service = FoodService()
