from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class UserCreateDTO(BaseModel):
    password: str
    email: str

class UserResponseDTO(BaseModel):
    id: UUID
    email: str
    password: str
    created_at: datetime
    updated_at: datetime
    