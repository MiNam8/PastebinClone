from dataclasses import dataclass
from datetime import datetime, timezone
import uuid 
from app.infrastructure.database.models import Users as UserModel
@dataclass
class User:
    id: str
    email: str
    password: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, email: str, password: str) -> 'User':
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            email=email,
            password=password,
            created_at=now,
            updated_at=now
        )

    @classmethod
    def from_model(cls, user_model: UserModel) -> 'User':
        return cls(
            id=str(user_model.id),
            email=user_model.email,
            password=user_model.password,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at
        )