# app/application/services/text_service.py
from app.domain.entities.text import Text as TextEntity
from app.infrastructure.database.models import Texts as TextModel
from app.application.dto.user_dto import UserCreateDTO
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from app.infrastructure.storage.s3_storage_service import S3StorageService
from app.infrastructure.cache.text_cache_service import TextCacheService
import threading
import logging

load_dotenv()

class TextService:
    def __init__(self, text_repository, cache_service: TextCacheService, storage_service: S3StorageService = None):
        self.text_repository = text_repository
        self.cache_service = cache_service
        self.storage_service = storage_service or S3StorageService()
        
        # Fix environment variable types
        self.default_ttl = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
        self.popular_ttl = int(os.getenv('POPULAR_CACHE_TTL_SECONDS', '7200'))
        self.popular_threshold = int(os.getenv('POPULAR_THRESHOLD', '10'))
        
        # Add lock for cache operations
        self._cache_lock = threading.RLock()

    def __enter__(self):
        """Context manager for resource management"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources"""
        cleanup_errors = []
        
        # Close database connections from repository
        try:
            if hasattr(self.text_repository, 'db') and hasattr(self.text_repository.db, 'close'):
                self.text_repository.db.close()
        except Exception as e:
            cleanup_errors.append(f"Database connection cleanup failed: {e}")
        
        # Close Redis connections from cache service
        try:
            if hasattr(self.cache_service, 'redis') and hasattr(self.cache_service.redis, 'close'):
                self.cache_service.redis.close()
        except Exception as e:
            cleanup_errors.append(f"Redis connection cleanup failed: {e}")
        
        # Log cleanup errors
        if cleanup_errors:
            logging.error(f"TextService cleanup errors: {'; '.join(cleanup_errors)}")
        
        # Don't suppress original exceptions
        return False

    def create_text(self, text: str, expiration_date: datetime) -> TextEntity:
        """Thread-safe text creation with proper resource cleanup"""
        
        s3_location = None
        text_entity = None
        
        try:
            # Step 1: Upload to S3 (can be done in parallel safely)
            s3_location = self.storage_service.upload_text(text)
            
            # Step 2: Create entity with S3 location
            text_entity = TextEntity.create(s3_location, expiration_date)
            
            # Step 3: Atomic database creation (includes hash consumption)
            return self.text_repository.create(text_entity)
            
        except Exception as e:
            # Compensating cleanup in reverse order
            if s3_location:
                try:
                    file_key = self.storage_service.parse_s3_location(s3_location)
                    self.storage_service.delete_text(file_key)
                    print(f"Cleaned up S3 file: {file_key}")
                except Exception as cleanup_error:
                    print(f"Failed to cleanup S3 file {s3_location}: {cleanup_error}")
                    # Log for manual cleanup
            
            # Re-raise original exception
            raise Exception(f"Failed to create text: {str(e)}") from e
    
    def get_text_metadata(self, hash_value: str) -> TextEntity:
        """Get text metadata only (no content)"""
        return self.text_repository.get_active_text(hash_value)
    
    def get_text_content_only(self, location: str) -> str:
        """Get text content from storage location"""
        file_key = self.storage_service.parse_s3_location(location)
        return self.storage_service.get_text_content(file_key)
    
    def get_full_text(self, hash_value: str) -> tuple[TextEntity, str]:
        """Get both metadata and content"""
        # Get metadata from database
        text_entity = self.text_repository.get_active_text(hash_value)
        if not text_entity:
            return None, None
        
        # Get content from storage
        content = self.get_text_content_only(text_entity.location)
        return text_entity, content
    
    def get_text_with_content(self, hash_value: str) -> dict:
        try:
            """Convenience method that returns everything"""
            text_entity, content = self.get_full_text(hash_value)
            if not text_entity:
                return None
            
            return {
                "metadata": text_entity,
                "content": content
            }
        
        except Exception as e:
            logging.error(f"Failed to get text {hash_value}: {str(e)}")
            return None

    def get_text(self, hash_value: str) -> dict:
        """Thread-safe cache check and population"""
        
        # Try atomic cache read first (if cache service supports it)
        complete_cached = self.cache_service.get_complete_text(hash_value)
        if complete_cached:
            return {**complete_cached, "from_cache": True}
        
        # If not in cache, use double-check locking pattern
        with self._cache_lock:
            # Double-check: maybe another thread just cached it
            complete_cached = self.cache_service.get_complete_text(hash_value)
            if complete_cached:
                return {**complete_cached, "from_cache": True}
            
            # Get from database/storage
            response = self.get_text_with_content(hash_value)
            if not response:
                return None
            
            # Atomically cache both metadata and content
            ttl = self._get_dynamic_ttl(hash_value)
            self.cache_service.cache_complete_text(
                hash_value, 
                response["metadata"], 
                response["content"], 
                ttl
            )
            
            return {
                "metadata": response["metadata"],
                "content": response["content"],
                "from_cache": False
            }
    
    def upload_text_to_s3(self, text: str) -> str:
        """
        Upload text content to S3
        
        Args:
            text: String content to upload
            
        Returns:
            S3 URL of the uploaded content
            
        Raises:
            Exception: If upload fails
        """
        try:
            return self.storage_service.upload_text(text)

        except ClientError as e:
            raise Exception(f"Failed to upload text to S3: {str(e)}")
        
    def get_text_from_s3(self, file_key: str) -> str:
        """
        Retrieve text content from an S3 file
        
        Args:
            file_key: The S3 object key (filename/path in bucket)
            
        Returns:
            String content of the file
            
        Raises:
            Exception: If retrieval fails
        """
        try:
            return self.storage_service.get_text_content(file_key)
        
        except ClientError as e:
            raise Exception(f"Failed to retrieve text from S3: {str(e)}")

    def get_text_content(self, location: str) -> str:
        """
        Get text content based on S3 location
        
        Args:
            location: S3 location (e.g., 's3://bucket-name/file-key')
            
        Returns:
            Text content
        """
        # Parse location to get the file key
        # Expected format: 's3://bucket-name/file-key'
        parts = location.replace('s3://', '').split('/', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 location format: {location}")
            
        bucket_name, file_key = parts
        
        # Check if this is the bucket we expect
        if bucket_name != os.getenv('BACKBLAZE_BUCKET_NAME'):
            raise ValueError(f"Unexpected bucket name: {bucket_name}")
        
        # Get the content
        return self.get_text_from_s3(file_key)
    

    def _get_dynamic_ttl(self, hash_value: str) -> int:
        """Thread-safe TTL calculation with error handling"""
        try:
            if self.cache_service.is_popular(hash_value, self.popular_threshold):
                return self.popular_ttl
            return self.default_ttl
        except Exception:
            # If popularity check fails, use default TTL
            return self.default_ttl

