# app/application/use_cases/auth_service.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.domain.entities.user import User as UserEntity
from app.infrastructure.database.models import Users as UserModel
from app.application.dto.user_dto import UserCreateDTO
import uuid
from fastapi import HTTPException
import os
import re

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

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
        
        if not self.validate_email(user_dto.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        hashed_password = pwd_context.hash(user_dto.password)
        user = UserEntity.create(user_dto.email, hashed_password)
        self.user_repository.create(user)
        return user
    
    def validate_email(self, email: str) -> bool:
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None
