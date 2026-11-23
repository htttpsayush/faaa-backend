from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.user import UserUpdate, UserResponse

class UserService:
    @staticmethod
    def update_profile(db: Session, current_user: User, user_in: UserUpdate) -> UserResponse:
        if user_in.email and user_in.email.lower() != current_user.email.lower():
            existing = user_repo.get_by_email(db, user_in.email)
            if existing and existing.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already taken by another account"
                )
        updated_user = user_repo.update(db, current_user, user_in)
        return UserResponse.model_validate(updated_user)

user_service = UserService()
