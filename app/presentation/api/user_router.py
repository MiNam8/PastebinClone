from fastapi import APIRouter, Depends, Response, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.application.services.user_service import AuthService
from sqlalchemy.orm import Session
from app.infrastructure.database.database import get_db
from app.infrastructure.repositories.user_repository_impl import SQLAlchemyUserRepository
from app.presentation.api.dependencies import get_current_user
from app.domain.entities.user import User
from pydantic import BaseModel
from app.application.dto.user_dto import UserCreateDTO
router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

def get_auth_service(db: Session = Depends(get_db)):
    repo = SQLAlchemyUserRepository(db)
    return AuthService(repo)

@router.post("/register")
def register(
    user_dto: UserCreateDTO,
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.register_user(user_dto)

@router.post("/login")
def login(
    response: Response,
    form_data:  LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = auth_service.create_access_token({"sub": user.email})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=1800,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    return {"message": "Login successful"}

@router.get("/me")
def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user
