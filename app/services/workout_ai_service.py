import json
from typing import List
from fastapi import HTTPException, status
from pydantic import ValidationError
from groq import Groq
from app.core.config import settings
from app.models.user import User
from app.repositories.workout_repo import workout_repo
from app.schemas.workout import (
    GeneratedExerciseItem,
    WorkoutGenerateRequest,
    WorkoutGenerateResponse
)
from app.services.progress_service import progress_service

WORKOUT_SYSTEM_PROMPT = """You are an elite strength, conditioning, and athletic performance coach.
Your job is to generate a personalized workout session based on the athlete's biometrics, recent history, and category parameters.

Return a STRICT JSON object in this exact format:
{
  "name": "Session Title (e.g. Upper Body Hypertrophy)",
  "category": "gym",
  "estimated_duration_min": 45,
  "exercises": [
    {
      "name": "Barbell Bench Press",
      "sets": 4,
      "reps": "8-10",
      "duration_sec": null,
      "rest_sec": 90,
      "notes": "Control the eccentric descent, explosive drive."
    }
  ]
}

Safety and Domain Rules:
1. "rehab" category:
   - NEVER diagnose injuries or medical conditions.
   - Prescribe only gentle general mobility, isometric holds, and low-load activation.
   - Always keep movements pain-free.
2. Return ONLY valid JSON, no markdown formatting, no conversational filler.
"""

class WorkoutAiService:
    @staticmethod
    def _get_groq_client() -> Groq:
        if not settings.GROQ_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Workout AI generation is unavailable because GROQ_API_KEY is not configured."
            )
        return Groq(api_key=settings.GROQ_API_KEY, timeout=25.0)

    @staticmethod
    def generate_workout(db, user: User, req: WorkoutGenerateRequest) -> WorkoutGenerateResponse:
        category = req.category.lower().strip()
        valid_categories = {"bodyweight", "gym", "speed", "endurance", "rehab"}
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category '{req.category}'. Must be one of: {', '.join(sorted(valid_categories))}"
            )

        # REHAB CRITICAL SAFETY CHECK:
        # If pain level is 7 or higher, do NOT generate exercises and refer to medical professional
        if category == "rehab" and (req.pain_level or 0) >= 7:
            return WorkoutGenerateResponse(
                name="Consult Healthcare Professional",
                category="rehab",
                estimated_duration_min=0,
                exercises=[],
                medical_disclaimer="General guidance only, not medical advice.",
                rehab_warning="Pain level is severe (7/10 or higher). Do not perform self-directed exercises. Please consult a qualified doctor or physiotherapist immediately."
            )

        # Gather user athletic context
        weight = user.weight_kg or 70.0
        height = user.height_cm or 175.0
        bmi_val, bmi_cat = progress_service.calculate_bmi(weight, height)

        # Last 5 workouts in this category for continuity
        recent_workouts = workout_repo.list_recent_by_category(db, user.id, category, limit=5)
        recent_history = [
            f"- {w.name} ({w.workout_date}): duration {w.duration_min}m, volume {w.volume_kg or 0}kg"
            for w in recent_workouts
        ]
        history_text = "\n".join(recent_history) if recent_history else "No prior sessions in this category."

        # Build prompt payload
        user_context_block = f"""
Athlete Biometrics:
- Weight: {weight} kg | Height: {height} cm | BMI: {bmi_val} ({bmi_cat})
Recent Category History (last 5 sessions):
{history_text}

Workout Request:
- Category: {category}
- Fitness Level: {req.level or 'intermediate'}
- Time Available: {req.time_available_min or 45} minutes
- Specific Focus: {req.focus or 'general'}
- Equipment: {req.equipment or 'standard'}
- Activity: {req.activity or 'general'}
- Target Distance: {req.target_distance_km or 'N/A'} km
- Body Area: {req.body_area or 'general'}
- Pain Level: {req.pain_level or 0}/10
- Rehab Stage: {req.stage or 'early'}
"""

        client = WorkoutAiService._get_groq_client()
        last_error = None

        for attempt in range(2):
            try:
                completion = client.chat.completions.create(
                    model=settings.GROQ_TEXT_MODEL,
                    messages=[
                        {"role": "system", "content": WORKOUT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_context_block}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                )
                content = completion.choices[0].message.content or "{}"
                data = json.loads(content)

                raw_exercises = data.get("exercises", [])
                parsed_exercises = [GeneratedExerciseItem.model_validate(ex) for ex in raw_exercises]

                return WorkoutGenerateResponse(
                    name=data.get("name", f"Personalized {category.capitalize()} Session"),
                    category=category,
                    estimated_duration_min=data.get("estimated_duration_min", req.time_available_min or 45),
                    exercises=parsed_exercises,
                    medical_disclaimer="General guidance only, not medical advice.",
                    rehab_warning=None
                )
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                if attempt == 1:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Failed to parse AI workout generation output. Please try again."
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Groq API error: {str(e)}"
                )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected failure during workout generation."
        )

workout_ai_service = WorkoutAiService()
