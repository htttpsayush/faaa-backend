from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.core.security import verify_password, create_access_token

class AuthService:
    @staticmethod
    def signup(db: Session, user_in: UserCreate) -> Token:
        existing = user_repo.get_by_email(db, user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists"
            )
        user = user_repo.create(db, user_in)
        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token, user=UserResponse.model_validate(user))

    @staticmethod
    def login(db: Session, creds: UserLogin) -> Token:
        user = user_repo.get_by_email(db, creds.email)
        if not user or not verify_password(creds.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token, user=UserResponse.model_validate(user))

auth_service = AuthService()
