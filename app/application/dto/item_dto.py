from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class ItemCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True

class ItemUpdateDTO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ItemResponseDTO(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True