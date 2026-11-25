import math
import re
from collections import Counter
from datetime import date, timedelta
from typing import Dict, List, Tuple
from fastapi import HTTPException, status
from groq import Groq
from sqlalchemy.orm import Session

from app.core.config import settings
from app.data.fitness_knowledge import FITNESS_KNOWLEDGE_CHUNKS
from app.models.user import User
from app.models.workout import Workout
from app.repositories.meal_repo import meal_repo
from app.schemas.coach import ChatMessage, CoachChatResponse
from app.services.diet_suggestion_service import DietSuggestionService

COACH_CR7_SYSTEM_PROMPT = """You are **Coach CR7**, an elite Cristiano Ronaldo-inspired performance, nutrition, and discipline coach inside PulseAI.

Personality & Coaching Style:
- Relentless work ethic, champion mentality, zero excuses, obsessed with consistency, clean nutrition, hydration, and sleep recovery.
- Sharp, motivating, direct, and actionable (2-4 concise paragraphs or crisp bullet points — never bloated essays).
- Reference the athlete's ACTUAL live numbers from the Retrieved Context below (calories, macro shortfalls, workout count/volume/dates, diet preference) so every answer feels personal.
- Respect the athlete's `diet_preference`: if "veg", suggest ONLY vegetarian Indian/whole foods; if "non_veg", include lean meats/eggs/fish or veg options.
- Rehab & Safety Rule: NEVER diagnose medical conditions or injuries. If the user reports sharp pain, injury, or pain >= 7/10, tell them to stop loading the area and consult a doctor or physiotherapist.

=== LIVE ATHLETE CONTEXT ===
{live_context}

=== RETRIEVED KNOWLEDGE BASE (TOP 3) ===
{knowledge_context}
"""


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


class RagCoachService:
    @staticmethod
    def _build_live_context(db: Session, user: User) -> Tuple[str, Dict[str, object], List[str]]:
        """Query live SQL data: user profile, today's meals/shortfalls, and last 7 days of workouts."""
        today = date.today()
        week_ago = today - timedelta(days=7)

        # 1. Today's nutrition & macro shortfalls
        today_meals = meal_repo.list_by_user_today(db, user.id, today)
        totals = meal_repo.get_daily_totals(db, user.id, today)
        cal_target = int(user.calorie_target or 2000)
        remaining_cals = round(max(0.0, cal_target - totals["calories"]), 1)
        shortfalls = DietSuggestionService.calculate_shortfalls(user, totals)

        # 2. Last 7 days of workouts
        recent_workouts = (
            db.query(Workout)
            .filter(
                Workout.user_id == user.id,
                Workout.workout_date >= week_ago,
            )
            .order_by(Workout.workout_date.desc(), Workout.id.desc())
            .all()
        )
        completed_count = sum(1 for w in recent_workouts if w.is_completed)
        total_duration = sum(int(w.duration_min or 0) for w in recent_workouts)
        total_volume = round(sum(float(w.volume_kg or 0.0) for w in recent_workouts), 1)

        diet_pref = (user.diet_preference or "any").lower()
        meal_names = ", ".join(m.name for m in today_meals[:6]) if today_meals else "None logged yet today"
        shortfall_str = (
            ", ".join(f"{s.nutrient}: -{s.shortfall_amount}{s.unit} (consumed {s.consumed}/{s.target}{s.unit})" for s in shortfalls)
            if shortfalls
            else "No major macro shortfalls (>10% under target)"
        )
        workout_lines = [
            f"- {w.workout_date}: {w.name} [{w.category}] ({w.duration_min} min, {w.volume_kg or 0} kg, {'done' if w.is_completed else 'planned'})"
            for w in recent_workouts[:7]
        ]
        workouts_str = "\n".join(workout_lines) if workout_lines else "No workouts logged in the last 7 days."

        live_text = (
            f"Athlete: {user.name} | Age: {user.age or 'N/A'} | Weight: {user.weight_kg or 'N/A'} kg | "
            f"Height: {user.height_cm or 'N/A'} cm | Diet Preference: {diet_pref}\n"
            f"Daily Calorie Target: {cal_target} kcal | Consumed Today: {round(totals['calories'], 1)} kcal | "
            f"Remaining: {remaining_cals} kcal\n"
            f"Today's Macros: Protein {round(totals['protein'], 1)}g, Carbs {round(totals['carbs'], 1)}g, Fats {round(totals['fats'], 1)}g\n"
            f"Macro Shortfalls: {shortfall_str}\n"
            f"Today's Meals ({len(today_meals)}): {meal_names}\n"
            f"Last 7 Days Training: {len(recent_workouts)} sessions ({completed_count} completed), "
            f"{total_duration} total min, {total_volume} kg total volume\n"
            f"{workouts_str}"
        )

        # Signals to enrich knowledge retrieval
        boost_tokens: List[str] = [diet_pref]
        if shortfalls:
            boost_tokens.extend(["macro", "shortfall", "protein", "meal", "swap"])
        if any((w.category or "").lower() == "rehab" for w in recent_workouts):
            boost_tokens.extend(["rehab", "injury", "safety"])
        if len(recent_workouts) == 0:
            boost_tokens.extend(["discipline", "consistency", "workout"])

        summary = {
            "calories_consumed": round(totals["calories"], 1),
            "calorie_target": cal_target,
            "workouts_7d": len(recent_workouts),
            "shortfalls_count": len(shortfalls),
        }
        return live_text, summary, boost_tokens

    @staticmethod
    def _retrieve_top_chunks(query: str, boost_tokens: List[str], top_k: int = 3) -> List[Dict[str, object]]:
        """Lightweight pure-Python TF-IDF + tag-overlap scorer (no ML libs, <1MB RAM)."""
        docs_tokens: List[List[str]] = []
        for chunk in FITNESS_KNOWLEDGE_CHUNKS:
            combined = f"{chunk['topic']} {' '.join(chunk['tags'])} {chunk['content']}"
            docs_tokens.append(_tokenize(combined))

        num_docs = len(docs_tokens)
        df: Counter = Counter()
        for tokens in docs_tokens:
            df.update(set(tokens))

        query_tokens = _tokenize(query) + [t.lower() for t in boost_tokens]
        query_counts = Counter(query_tokens)

        scored: List[Tuple[float, Dict[str, object]]] = []
        for idx, chunk in enumerate(FITNESS_KNOWLEDGE_CHUNKS):
            doc_counts = Counter(docs_tokens[idx])
            doc_len = max(1, len(docs_tokens[idx]))
            tag_set = {str(t).lower() for t in chunk["tags"]}

            score = 0.0
            for term, q_freq in query_counts.items():
                if term in doc_counts:
                    tf = doc_counts[term] / doc_len
                    idf = math.log((num_docs + 1) / (df[term] + 1)) + 1.0
                    tag_bonus = 0.35 if term in tag_set else 0.0
                    score += q_freq * (tf * idf + tag_bonus)

            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    @staticmethod
    def chat(db: Session, user: User, message: str, history: List[ChatMessage]) -> CoachChatResponse:
        if not settings.GROQ_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Groq API key is not configured. Add GROQ_API_KEY in backend/.env to enable Coach CR7.",
            )

        live_context, context_summary, boost_tokens = RagCoachService._build_live_context(db, user)
        top_chunks = RagCoachService._retrieve_top_chunks(message, boost_tokens, top_k=3)
        knowledge_context = "\n\n".join(
            f"[{c['topic']}]\n{c['content']}" for c in top_chunks
        )

        system_prompt = COACH_CR7_SYSTEM_PROMPT.format(
            live_context=live_context,
            knowledge_context=knowledge_context,
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in history[-8:]:
            messages.append({"role": turn.role, "content": turn.content})
        messages.append({"role": "user", "content": message})

        model_name = getattr(settings, "GROQ_MODEL", None) or "openai/gpt-oss-120b"
        client = Groq(api_key=settings.GROQ_API_KEY, timeout=25.0)

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.6,
                max_tokens=700,
            )
            reply = (completion.choices[0].message.content or "").strip()
            if not reply:
                reply = "Stay focused, athlete. Log your next meal and hit your session — no excuses."
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Coach CR7 could not reach Groq right now: {str(exc)}",
            )

        return CoachChatResponse(
            reply=reply,
            retrieved_topics=[str(c["topic"]) for c in top_chunks],
            context_summary=context_summary,
        )


rag_coach_service = RagCoachService()
