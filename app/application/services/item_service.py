from typing import List, Optional
from app.domain.entities.item import Item
from app.domain.repositories.item_repository import ItemRepository
from app.application.dto.item_dto import ItemCreateDTO, ItemUpdateDTO, ItemResponseDTO

class ItemService:
    def __init__(self, item_repository: ItemRepository):
        self._item_repository = item_repository

    def create_item(self, item_dto: ItemCreateDTO) -> ItemResponseDTO:
        item = Item.create(
            title=item_dto.title,
            description=item_dto.description
        )
        created_item = self._item_repository.create(item)
        return ItemResponseDTO.model_validate(created_item)

    def get_item(self, item_id: str) -> Optional[ItemResponseDTO]:
        item = self._item_repository.get_by_id(item_id)
        if item:
            return ItemResponseDTO.model_validate(item)
        return None

    def get_items(self, skip: int = 0, limit: int = 100) -> List[ItemResponseDTO]:
        items = self._item_repository.get_all(skip, limit)
        return [ItemResponseDTO.model_validate(item) for item in items]

    def update_item(self, item_id: str, item_dto: ItemUpdateDTO) -> Optional[ItemResponseDTO]:
        item = self._item_repository.get_by_id(item_id)
        if not item:
            return None

        item.update(
            title=item_dto.title,
            description=item_dto.description,
            is_active=item_dto.is_active
        )
        updated_item = self._item_repository.update(item)
        return ItemResponseDTO.model_validate(updated_item)

    def delete_item(self, item_id: str) -> bool:
        return self._item_repository.delete(item_id)