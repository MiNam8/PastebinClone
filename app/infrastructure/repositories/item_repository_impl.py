from uuid import UUID
from typing import List, Optional
from sqlmodel import Session, select
from app.domain.entities.item import Item as ItemEntity
from app.domain.repositories.item_repository import ItemRepository
from app.infrastructure.database.models import Items as ItemModel

class SQLModelItemRepository(ItemRepository):
    def __init__(self, db: Session):
        self._db = db

    def create(self, item: ItemEntity) -> ItemEntity:
        item_model = ItemModel(
            title=item.title,
            description=item.description,
            is_active=item.is_active
        )
        self._db.add(item_model)
        self._db.commit()
        self._db.refresh(item_model)
        return self._to_domain(item_model)

    def get_by_id(self, item_id: str) -> Optional[ItemEntity]:
        try:
            uuid_id = UUID(item_id)
            db_item = self._db.get(ItemModel, uuid_id)
            if not db_item:
                return None
            return self._to_domain(db_item)
        except ValueError:
            return None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ItemEntity]:
        db_items = self._db.exec(select(ItemModel).offset(skip).limit(limit)).all()
        return [self._to_domain(item) for item in db_items]

    def update(self, item: ItemEntity) -> ItemEntity:
        try:
            uuid_id = UUID(str(item.id)) if item.id else None
            db_item = self._db.get(ItemModel, uuid_id)
            if not db_item:
                return None
                
            db_item.title = item.title
            db_item.description = item.description
            db_item.is_active = item.is_active
            
            self._db.commit()
            self._db.refresh(db_item)
            return self._to_domain(db_item)
        except ValueError:
            return None

    def delete(self, item_id: str) -> bool:
        try:
            uuid_id = UUID(item_id)
            db_item = self._db.get(ItemModel, uuid_id)
            if not db_item:
                return False
            self._db.delete(db_item)
            self._db.commit()
            return True
        except ValueError:
            return False

    def _to_domain(self, db_item: ItemModel) -> ItemEntity:
        return ItemEntity(
            id=str(db_item.id),
            title=db_item.title,
            description=db_item.description,
            is_active=db_item.is_active,
            created_at=db_item.created_at,
            updated_at=db_item.updated_at
        )