from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class Item:
    id: Optional[int]
    title: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, title: str, description: Optional[str] = None) -> 'Item':
        now = datetime.now(timezone.utc)
        return cls(
            id=None,
            title=title,
            description=description,
            is_active=True,
            created_at=now,
            updated_at=now
        )

    def update(self, title: Optional[str] = None, description: Optional[str] = None, is_active: Optional[bool] = None) -> None:
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if is_active is not None:
            self.is_active = is_active
        self.updated_at = datetime.now(timezone.utc)