from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.infrastructure.database.database import get_db
from app.infrastructure.repositories.item_repository_impl import SQLModelItemRepository
from app.application.services.item_service import ItemService
from app.application.dto.item_dto import ItemCreateDTO, ItemUpdateDTO, ItemResponseDTO
from app.domain.entities.user import User
from app.presentation.api.dependencies import get_current_user

router = APIRouter()

def get_item_service(db: Session = Depends(get_db)) -> ItemService:
    repository = SQLModelItemRepository(db)
    return ItemService(repository)

@router.post("/items/", response_model=ItemResponseDTO)
def create_item(
    item_dto: ItemCreateDTO,
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user)
):
    return item_service.create_item(item_dto)

@router.get("/items/", response_model=List[ItemResponseDTO])
def read_items(
    skip: int = 0,
    limit: int = 100,
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user)
):
    return item_service.get_items(skip, limit)

@router.get("/items/{item_id}", response_model=ItemResponseDTO)
def read_item(
    item_id: str,
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user)
):
    item = item_service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/items/{item_id}", response_model=ItemResponseDTO)
def update_item(
    item_id: str,
    item_dto: ItemUpdateDTO,
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user)
):
    item = item_service.update_item(item_id, item_dto)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/items/{item_id}")
def delete_item(
    item_id: str,
    item_service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user)
):
    success = item_service.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}