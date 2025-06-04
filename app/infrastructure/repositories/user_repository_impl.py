# app/adapters/outbound/persistence/user_repository_impl.py
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import Users as UserModel
from sqlmodel import select
from app.domain.entities.user import User as UserEntity
class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db):
        self.db = db

    def create(self, user: User) -> UserModel:
        user_model = UserModel(
            email=user.email,
            password=user.password
        )
        self.db.add(user_model)
        self.db.commit()
        self.db.refresh(user_model)
        return UserEntity.from_model(user_model)

    def get_by_email(self, email: str) -> UserEntity:
        user = self.db.exec(select(UserModel).where(UserModel.email == email)).first()
        if not user:
            return None
        return UserEntity.from_model(user)
