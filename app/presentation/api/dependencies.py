# app/presentation/api/dependencies.py
from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from app.infrastructure.database.database import get_db
from app.infrastructure.repositories.user_repository_impl import SQLAlchemyUserRepository
from app.application.services.user_service import AuthService

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def get_current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        repo = SQLAlchemyUserRepository(db)
        auth_service = AuthService(repo)
        user = auth_service.get_user_by_username(username)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")