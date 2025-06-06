# app/adapters/outbound/persistence/user_repository_impl.py
from app.domain.entities.text import Text
from app.domain.repositories.text_repository import TextRepository
from app.infrastructure.database.models import Texts as TextModel
from sqlmodel import select
from app.domain.entities.text import Text as TextEntity
from redis import Redis
import os
import time
import uuid
import random
from datetime import datetime, timezone
from sqlmodel import Session
from typing import Optional

class SQLAlchemyTextRepository(TextRepository):
    def __init__(self, db, redis_client: Redis = None, hash_threshold: int = 10):
        self.db = db
        self.redis = redis_client
        self.hash_threshold = hash_threshold
        self.hash_queue_key = "text_hash_queue"
        self.hash_generation_lock = "hash_generation_lock"
        self.hash_request_stream = "hash_generation_requests"
        self.service_id = os.getenv("SERVICE_ID", "text-service-1")
        
        # NEW: Atomic check-consume-or-request script
        self.atomic_check_consume_script = """
            local queue_key = KEYS[1]
            local lock_key = KEYS[2]
            local stream_key = KEYS[3]
            local threshold = tonumber(ARGV[1])
            local lock_ttl = tonumber(ARGV[2])
            local batch_size = ARGV[3]
            local service_id = ARGV[4]
            local request_id = ARGV[5]
            
            -- Try to consume a hash first
            local hash_value = redis.call('LPOP', queue_key)
            local queue_length = redis.call('LLEN', queue_key)
            
            if hash_value then
                -- Success: got a hash
                return {
                    'status', 'success',
                    'hash', hash_value,
                    'queue_length', queue_length
                }
            end
            
            -- No hash available, check if we need to request generation
            if queue_length < threshold then
                -- Try to acquire lock for hash generation
                local lock_acquired = redis.call('SET', lock_key, service_id, 'NX', 'EX', lock_ttl)
                
                if lock_acquired then
                    -- Send generation request
                    local message = {
                        'batch_size', batch_size,
                        'requesting_service', service_id,
                        'timestamp', redis.call('TIME')[1],
                        'request_id', request_id,
                        'lock_key', lock_key,
                        'queue_length', queue_length
                    }
                    
                    local message_id = redis.call('XADD', stream_key, '*', unpack(message))
                    
                    return {
                        'status', 'generation_requested',
                        'message_id', message_id,
                        'queue_length', queue_length,
                        'lock_acquired', 1
                    }
                else
                    -- Someone else is already requesting
                    return {
                        'status', 'generation_in_progress',
                        'queue_length', queue_length,
                        'lock_acquired', 0
                    }
                end
            else
                -- Queue has enough hashes but all consumed by other threads
                return {
                    'status', 'temporarily_unavailable',
                    'queue_length', queue_length
                }
            end
        """
        
        # Register the script
        self.atomic_script = self.redis.register_script(self.atomic_check_consume_script)
    
    def check_hash_availability(self):
        """Atomically check availability and acquire lock if needed"""
        if not self.redis:
            raise Exception("Redis is not available")
        
        result = self.redis.eval(
            self.check_and_lock_script,
            2,  # Number of keys
            self.hash_queue_key,
            self.hash_generation_lock,
            str(self.hash_threshold),
            "60"  # Lock TTL in seconds
        )
        
        queue_length, lock_status = result
        
        if lock_status == 1:  # Lock acquired
            self._request_hash_generation()
        elif lock_status == 0:  # Lock already exists
            print("Hash generation already in progress")
        # lock_status == -1 means above threshold, no action needed
        
        return queue_length
    
    def _request_hash_generation(self):
        """Request hash generation - lock remains until hashes are available"""
        if not self.redis:
            raise Exception("Redis is not available")
        
        try:
            batch_size = os.getenv("HASH_BATCH_SIZE", "100")
            
            message = {
                "batch_size": batch_size,
                "requesting_service": self.service_id,
                "timestamp": str(int(time.time())),
                "request_id": str(uuid.uuid4()),
                "lock_key": self.hash_generation_lock  # Include lock key in message
            }
            
            message_id = self.redis.xadd(self.hash_request_stream, message)
            print(f"Requested hash generation via Redis Stream. Message ID: {message_id}")
            
            # DON'T release lock here - let the hash generation service release it
            # when it adds hashes to the queue
            
        except Exception as e:
            print(f"Error requesting hash generation: {str(e)}")
            # Only release lock on error
            self.redis.delete(self.hash_generation_lock)

    def _extend_lock_if_needed(self):
        """Extend lock TTL if hash generation is taking longer than expected"""
        current_ttl = self.redis.ttl(self.hash_generation_lock)
        if current_ttl is not None and current_ttl < 10:  # Less than 10 seconds left
            self.redis.expire(self.hash_generation_lock, 60)  # Extend by 60 seconds

    def create(self, text: Text, max_retries: int = 5) -> TextEntity:
        """Create text with atomic hash consumption and proper cleanup"""
        
        consumed_hash = None
        db_transaction_started = False
        
        try:
            # Start database transaction
            self.db.begin()
            db_transaction_started = True
            
            # Atomic hash consumption with intelligent retry
            consumed_hash = self._atomic_consume_hash_with_retry(max_retries)
            
            if not consumed_hash:
                raise Exception("Failed to acquire hash after all retries")
            
            # Create database record
            text_model = TextModel(
                id=text.id,
                location=text.location,
                expiration_date=text.expiration_date,
                hash_value=consumed_hash,
                created_at=text.created_at,
                updated_at=text.updated_at
            )
            
            self.db.add(text_model)
            self.db.commit()
            self.db.refresh(text_model)
            
            return TextEntity.from_model(text_model)
            
        except Exception as e:
            # Compensating transaction: cleanup in reverse order
            if db_transaction_started:
                self.db.rollback()
            
            if consumed_hash:
                self._return_hash_to_queue(consumed_hash)
            
            raise e

    def _atomic_consume_hash_with_retry(self, max_retries: int) -> str:
        """Atomically consume hash with intelligent retry strategy"""
        
        for attempt in range(max_retries):
            try:
                # Execute atomic script
                result = self.atomic_script(
                    keys=[
                        self.hash_queue_key,
                        self.hash_generation_lock, 
                        self.hash_request_stream
                    ],
                    args=[
                        str(self.hash_threshold),
                        "60",  # Lock TTL
                        os.getenv("HASH_BATCH_SIZE", "100"),
                        self.service_id,
                        str(uuid.uuid4())
                    ]
                )
                
                # Parse result
                result_dict = self._parse_lua_result(result)
                status = result_dict['status']
                
                if status == 'success':
                    return result_dict['hash']
                    
                elif status == 'generation_requested':
                    print(f"Hash generation requested. Message ID: {result_dict.get('message_id')}")
                    delay = self._calculate_generation_delay(attempt)
                    
                elif status == 'generation_in_progress': 
                    print("Hash generation already in progress")
                    delay = self._calculate_wait_delay(attempt)
                    
                elif status == 'temporarily_unavailable':
                    print("Hashes temporarily unavailable")
                    delay = self._calculate_backoff_delay(attempt)
                    
                else:
                    raise Exception(f"Unknown status: {status}")
                
                # Wait before retry (except on last attempt)
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s")
                    time.sleep(delay)
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = self._calculate_error_delay(attempt)
                    print(f"Error on attempt {attempt + 1}: {str(e)}, retrying in {delay:.2f}s")
                    time.sleep(delay)
                else:
                    raise e
        
        return None

    def _parse_lua_result(self, result: list) -> dict:
        """Convert Lua script result to dictionary"""
        result_dict = {}
        for i in range(0, len(result), 2):
            key = result[i].decode() if isinstance(result[i], bytes) else result[i]
            value = result[i + 1]
            if isinstance(value, bytes):
                value = value.decode()
            result_dict[key] = value
        return result_dict

    def _return_hash_to_queue(self, hash_value: str):
        """Return unused hash back to queue (compensating action)"""
        try:
            if self.redis and hash_value:
                self.redis.lpush(self.hash_queue_key, hash_value)
                print(f"Returned hash {hash_value} to queue")
        except Exception as e:
            print(f"Failed to return hash to queue: {str(e)}")
            # Log this for manual intervention

    def _calculate_generation_delay(self, attempt: int) -> float:
        """Calculate delay when waiting for hash generation"""
        # Longer delays since generation takes time
        base_delay = 2.0
        return base_delay * (1.5 ** attempt) + random.uniform(0, 1)

    def _calculate_wait_delay(self, attempt: int) -> float:
        """Calculate delay when generation is already in progress"""
        # Shorter delays since we're just waiting
        base_delay = 0.5
        return base_delay * (1.2 ** attempt) + random.uniform(0, 0.5)

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        base_delay = 0.1
        return base_delay * (2 ** attempt) + random.uniform(0, 0.2)

    def _calculate_error_delay(self, attempt: int) -> float:
        """Calculate delay for error scenarios"""
        base_delay = 1.0
        return base_delay * (2 ** attempt) + random.uniform(0, 1)

    def get_text(self, hash_value: str) -> TextEntity:
        """Get text metadata from database"""
        text_model = self.db.exec(
            select(TextModel).where(TextModel.hash_value == hash_value)
        ).one_or_none()
        
        if text_model:
            return TextEntity.from_model(text_model)
        return None

    def health_check(self) -> dict:
        """Monitor the health of your Points 1-3 implementation"""
        if not self.redis:
            return {"status": "unhealthy", "reason": "Redis unavailable"}
        
        try:
            queue_length = self.redis.llen(self.hash_queue_key)
            lock_exists = self.redis.exists(self.hash_generation_lock)
            lock_ttl = self.redis.ttl(self.hash_generation_lock) if lock_exists else None
            
            # Detect stuck locks (Point 2 monitoring)
            if lock_exists and (lock_ttl is None or lock_ttl < 5):
                print("Detected potentially stuck lock, releasing...")
                self.redis.delete(self.hash_generation_lock)
            
            return {
                "status": "healthy",
                "queue_length": queue_length,
                "lock_exists": bool(lock_exists),
                "lock_ttl": lock_ttl,
                "atomic_operations": "lua_scripts",  # Point 1 status
                "retry_capability": True,  # Point 3 status
            }
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}

    def get_active_text(self, hash_value: str) -> Optional[TextModel]:
        """Get text only if it hasn't expired"""
        statement = select(TextModel).where(
            TextModel.hash_value == hash_value,
            # Text is active if expiration_date is None OR expiration_date > now
            (TextModel.expiration_date.is_(None)) | 
            (TextModel.expiration_date > datetime.now(timezone.utc))
        )
        return self.db.exec(statement).first()
    
    def get_all_active_texts(self) -> list[TextModel]:
        """Get all non-expired texts"""
        statement = select(TextModel).where(
            (TextModel.expiration_date.is_(None)) | 
            (TextModel.expiration_date > datetime.now(timezone.utc))
        )
        return self.db.exec(statement).all()
    
    def cleanup_expired_texts(self) -> int:
        """Remove expired texts - run this as a background job"""
        statement = select(TextModel).where(
            TextModel.expiration_date.is_not(None),
            TextModel.expiration_date <= datetime.now(timezone.utc)
        )
        expired_texts = self.db.exec(statement).all()
        
        for text in expired_texts:
            self.db.delete(text)
        
        self.db.commit()
        return len(expired_texts)
