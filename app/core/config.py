import json
import os
from typing import List
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

class Settings:
    PROJECT_NAME: str = "PulseAI"
    API_V1_STR: str = "/api/v1"
    PORT: int = int(os.getenv("PORT", "8000"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pulseai.db")

    # SECRET_KEY must be provided via environment (.env); no insecure hardcoded fallback
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is missing. Set SECRET_KEY in your .env file.")

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Groq AI settings (reads from environment; empty by default)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_VISION_MODEL: str = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")
    GROQ_TEXT_MODEL: str = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")

    # Single source of truth for diet target and shortfall calculations
    DIET_TARGETS_CONFIG: dict = {
        "PROTEIN_GRAMS_PER_KG": 1.6,
        "FATS_CALORIE_PERCENT": 0.25,
        "CALORIES_PER_FAT_GRAM": 9.0,
        "CALORIES_PER_CARB_GRAM": 4.0,
        "CALORIES_PER_PROTEIN_GRAM": 4.0,
        "SHORTFALL_THRESHOLD_PCT": 0.10,  # Nutrient is short if >10% below target
    }

    @property
    def cors_origins(self) -> List[str]:
        raw = os.getenv("CORS_ORIGINS", '["*"]')
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
            return [raw]
        except Exception:
            return [origin.strip() for origin in raw.split(",") if origin.strip()] or ["*"]

def normalize_database_url(url: str) -> str:
    """Normalize Postgres URLs to use the psycopg (v3) dialect consistently."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


settings = Settings()
