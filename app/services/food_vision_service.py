import base64
import json
from typing import List
from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError
from groq import Groq
from app.core.config import settings
from app.schemas.meal import AnalyzedFoodItem, PhotoAnalysisResponse

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

VISION_SYSTEM_PROMPT = """You are an expert sports nutrition analysis assistant.
Analyze the meal in the photo and estimate the food items with their macronutrients.

Return a STRICT JSON object in this exact format:
{
  "items": [
    {
      "name": "Food Item Name",
      "estimated_grams": 150.0,
      "calories": 250.0,
      "protein_g": 25.0,
      "carbs_g": 15.0,
      "fats_g": 8.0,
      "confidence": 0.85,
      "needs_input": false,
      "reason": "Clear visible grilled chicken with salad"
    }
  ]
}

Rules:
1. Estimate reasonable portion weights (estimated_grams) and macros based on typical preparation.
2. Confidence must be a float between 0.0 and 1.0.
3. If an item is blurry, hidden, ambiguous, or you are unsure about its portion or macros, you MUST set the unsure numbers to null, set needs_input to true, and explain why in reason.
4. If no food is recognized in the image, return {"items": []}.
5. Return ONLY valid JSON, nothing else.
"""

class FoodVisionService:
    @staticmethod
    def _get_groq_client() -> Groq:
        if not settings.GROQ_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI photo analysis is currently unavailable because the Groq API key is not configured."
            )
        return Groq(api_key=settings.GROQ_API_KEY, timeout=30.0)

    @staticmethod
    async def analyze_photo(file: UploadFile) -> PhotoAnalysisResponse:
        # 1. Validate content type
        content_type = file.content_type or ""
        if content_type.lower() not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Supported formats: JPEG, PNG, WEBP."
            )

        # 2. Read bytes in-memory and validate size (max 5MB)
        image_bytes = await file.read()
        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file is too large. Maximum allowed size is 5 MB."
            )

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        client = FoodVisionService._get_groq_client()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{content_type};base64,{base64_image}"

        # 3. Call Groq vision model with 1 retry on invalid JSON
        parsed_items: List[AnalyzedFoodItem] = []
        last_error = None

        for attempt in range(2):
            try:
                completion = client.chat.completions.create(
                    model=settings.GROQ_VISION_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": VISION_SYSTEM_PROMPT},
                                {"type": "image_url", "image_url": {"url": data_url}}
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )

                content = completion.choices[0].message.content or "{}"
                data = json.loads(content)
                raw_items = data.get("items", [])

                parsed_items = [AnalyzedFoodItem.model_validate(item) for item in raw_items]
                break
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                if attempt == 1:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Failed to parse AI food analysis output. Please try again or log manually."
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Groq vision API error: {str(e)}"
                )

        return PhotoAnalysisResponse(
            items=parsed_items,
            is_estimate=True,
            message="Values are estimated from the photo. Review or adjust values before saving."
        )

food_vision_service = FoodVisionService()
