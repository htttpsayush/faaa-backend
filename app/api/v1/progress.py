from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.progress import ProgressSummaryResponse
from app.services.progress_service import progress_service

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.get("/summary", response_model=ProgressSummaryResponse)
def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return progress_service.get_summary(db, current_user)
