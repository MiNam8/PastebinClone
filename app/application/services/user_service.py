# app/application/use_cases/auth_service.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.domain.entities.user import User as UserEntity
from app.infrastructure.database.models import Users as UserModel
from app.application.dto.user_dto import UserCreateDTO
import uuid
from fastapi import HTTPException
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def authenticate_user(self, email: str, password: str) -> UserEntity:
        user = self.user_repository.get_by_email(email)
        if not user or not pwd_context.verify(password, user.password):
            return None
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def register_user(self, user_dto: UserCreateDTO) -> UserEntity:
        if self.user_repository.get_by_email(user_dto.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = pwd_context.hash(user_dto.password)
        user = UserEntity.create(user_dto.email, hashed_password)
        self.user_repository.create(user)
        return user
