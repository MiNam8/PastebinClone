from dataclasses import dataclass
from datetime import datetime, timezone
import uuid 
from app.infrastructure.database.models import Texts as TextModel
from typing import Dict, Any
import json

@dataclass
class Text:
    id: int
    location: str
    expiration_date: datetime
    hash_value: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, location: str, expiration_date: datetime) -> 'Text':
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            location=location,
            expiration_date=expiration_date,
            hash_value=None,
            created_at=now,
            updated_at=now
        )

    @classmethod
    def from_model(cls, text_model: TextModel) -> 'Text':
        return cls(
            id=text_model.id,
            location=text_model.location,
            expiration_date=text_model.expiration_date,
            hash_value=text_model.hash_value,
            created_at=text_model.created_at,
            updated_at=text_model.updated_at
        )

    def to_dict(self) -> dict:
        """Convert entity to dictionary for serialization"""
        return {
            "id": self.id,
            "location": self.location,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "hash_value": getattr(self, 'hash_value', None),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Text':
        """Create entity from dictionary (for deserialization)"""
        from datetime import datetime
        from uuid import UUID
        
        return cls(
            id=UUID(data["id"]),
            location=data["location"],
            expiration_date=datetime.fromisoformat(data["expiration_date"]),
            hash_value=data.get("hash_value"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )