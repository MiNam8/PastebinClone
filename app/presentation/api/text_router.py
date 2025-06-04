from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.database.database import get_db
from app.infrastructure.repositories.text_repository import SQLAlchemyTextRepository
from pydantic import BaseModel
from app.application.services.text_service import TextService
from datetime import datetime
from app.infrastructure.database.redis_client import get_redis_client
from redis import Redis
import os
from app.infrastructure.storage.s3_storage_service import S3StorageService
from app.infrastructure.cache.text_cache_service import TextCacheService

router = APIRouter()

class TextRequest(BaseModel):
    text: str
    expiration_date: datetime

def get_text_service(
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis_client)
):
    repo = SQLAlchemyTextRepository(db, redis_client, os.getenv("HASH_BATCH_SIZE"))
    cache_service = TextCacheService(redis_client)
    storage_service = S3StorageService()
    return TextService(repo, cache_service, storage_service)

@router.post("/text")
def create_text(
    request: TextRequest,
    text_service: TextService = Depends(get_text_service)
):
    return text_service.create_text(request.text, request.expiration_date)

@router.get("/text/{hash_value}")
def get_text(
    hash_value: str,
    response: Response,
    text_service: TextService = Depends(get_text_service)
):
    result = text_service.get_text(hash_value)
    if not result:
        raise HTTPException(status_code=404, detail="Text not found")
    
    if result.get("from_cache"):
        response.headers["X-Cache"] = "HIT"
        response.headers["Cache-Control"] = "public, max-age=3600"
    else:
        response.headers["X-Cache"] = "MISS"
        response.headers["Cache-Control"] = "public, max-age=1800"
    
    return {
        "content": result,
        "headers": {
            "X-Text-Hash": hash_value,
            "X-Created-At": result["metadata"].created_at.isoformat()
        }
    }