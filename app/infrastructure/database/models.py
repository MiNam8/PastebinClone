from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4

class ItemBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)

class Items(ItemBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    password: str

class Users(UserBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )

class TextBase(SQLModel):
    location: str
    expiration_date: datetime
    hash_value: str = Field(primary_key=True)

class Texts(TextBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )