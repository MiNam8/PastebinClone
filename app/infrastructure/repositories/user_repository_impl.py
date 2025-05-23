# app/adapters/outbound/persistence/user_repository_impl.py
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import Users as UserModel
from sqlmodel import select

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db):
        self.db = db

    def get_by_username(self, username: str):
        user = self.db.exec(select(UserModel).where(UserModel.username == username)).first()
        if not user:
            return None
        return User(id=user.id, username=user.username, hashed_password=user.hashed_password)
