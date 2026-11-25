from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.coach import CoachChatRequest, CoachChatResponse
from app.services.rag_coach_service import rag_coach_service

router = APIRouter(prefix="/coach", tags=["Coach"])


@router.post("/chat", response_model=CoachChatResponse)
def coach_chat(
    req: CoachChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hybrid RAG AI Fitness Coach ("Coach CR7") using live SQL stats + curated knowledge."""
    return rag_coach_service.chat(db, current_user, req.message, req.history)
