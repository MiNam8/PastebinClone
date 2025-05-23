from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4

class ItemBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)

class Items(ItemBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(datetime.UTC)}
    )

class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    hashed_password: str

class Users(UserBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)