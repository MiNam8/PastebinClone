from typing import List, Optional
from sqlmodel import Session, select
from app.domain.entities.item import Item
from app.domain.repositories.item_repository import ItemRepository
from app.infrastructure.database.models import Item as ItemModel

class SQLModelItemRepository(ItemRepository):
    def __init__(self, db: Session):
        self._db = db

    def create(self, item: Item) -> Item:
        self._db.add(item)
        self._db.commit()
        self._db.refresh(item)
        return item

    def get_by_id(self, item_id: int) -> Optional[Item]:
        item = self._db.get(ItemModel, item_id)
        if not item:
            return None
        return item


    def get_all(self, skip: int = 0, limit: int = 100) -> List[Item]:
        items = self._db.exec(select(ItemModel).offset(skip).limit(limit)).all()
        return items

    def update(self, item: Item) -> Item:
        item = self._db.get(ItemModel, item.id)
        if not item:
            return None
        for field, value in item.model_dump().items():
            setattr(item, field, value)
        self._db.commit()
        self._db.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        item = self._db.get(ItemModel, item_id)
        if not item:
            return False
        self._db.delete(item)
        self._db.commit()
        return item

    def _to_domain(self, db_item: ItemModel) -> Item:
        return Item(
            id=db_item.id,
            title=db_item.title,
            description=db_item.description,
            is_active=db_item.is_active,
            created_at=db_item.created_at,
            updated_at=db_item.updated_at
        )