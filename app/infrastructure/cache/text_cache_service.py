from redis import Redis
import json
import os
from datetime import timedelta
from app.domain.entities.text import Text as TextEntity

class TextCacheService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.metadata_prefix = "text_meta:"
        self.content_prefix = "text_content:"
        self.popularity_prefix = "text_popularity:"
        self.default_ttl = int(os.getenv("CACHE_TTL_SECONDS", "10800"))  # 3 hours
        self.popular_ttl = int(os.getenv("POPULAR_CACHE_TTL_SECONDS", "21600"))  # 6 hours
        
        # Lua script for atomic get-and-increment
        self._get_and_increment_script = self.redis.register_script("""
            local key = KEYS[1]
            local popularity_key = KEYS[2]
            local cached = redis.call('GET', key)
            if cached then
                redis.call('ZINCRBY', popularity_key, 1, ARGV[1])
                redis.call('EXPIRE', popularity_key, 86400)
                return cached
            else
                return nil
            end
        """)
        
        # New Lua script for complete text with popularity
        self._get_complete_text_script = self.redis.register_script("""
            local meta_key = KEYS[1]
            local content_key = KEYS[2]
            local popularity_key = KEYS[3]
            local hash_value = ARGV[1]
            
            local metadata = redis.call('GET', meta_key)
            local content = redis.call('GET', content_key)
            
            if metadata and content then
                redis.call('ZINCRBY', popularity_key, 1, hash_value)
                redis.call('EXPIRE', popularity_key, 86400)
                return {metadata, content}
            else
                return nil
            end
        """)
    
    def get_text_metadata(self, hash_value: str) -> TextEntity:
        """Thread-safe get with popularity increment"""
        cached = self._get_and_increment_script(
            keys=[
                f"{self.metadata_prefix}{hash_value}",
                f"{self.popularity_prefix}daily"
            ],
            args=[hash_value]
        )
        
        if cached:
            return TextEntity.from_dict(json.loads(cached))
        return None
    
    def cache_text_metadata(self, hash_value: str, text_entity: TextEntity, ttl: int = None):
        """Cache text metadata"""
        ttl = ttl or self.default_ttl
        self.redis.setex(
            f"{self.metadata_prefix}{hash_value}",
            ttl,
            json.dumps(text_entity.to_dict())
        )
    
    def get_text_content(self, hash_value: str) -> str:
        """Thread-safe get with popularity increment"""
        cached = self._get_and_increment_script(
            keys=[
                f"{self.content_prefix}{hash_value}",
                f"{self.popularity_prefix}daily"
            ],
            args=[hash_value]
        )
        
        return cached.decode('utf-8') if cached else None
    
    def cache_text_content(self, hash_value: str, content: str, ttl: int = None):
        """Cache text content"""
        ttl = ttl or self.default_ttl
        self.redis.setex(
            f"{self.content_prefix}{hash_value}",
            ttl,
            content
        )
    
    def _increment_popularity(self, hash_value: str):
        """Thread-safe popularity increment with error handling"""
        try:
            # ZINCRBY is atomic in Redis
            pipe = self.redis.pipeline()
            pipe.zincrby(f"{self.popularity_prefix}daily", 1, hash_value)
            pipe.expire(f"{self.popularity_prefix}daily", 86400)
            pipe.execute()
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Failed to increment popularity for {hash_value}: {e}")
    
    def get_popular_texts(self, limit: int = 100) -> list:
        """Get most popular text hashes"""
        return self.redis.zrevrange(f"{self.popularity_prefix}daily", 0, limit-1)
    
    def is_popular(self, hash_value: str, threshold: int = 10) -> bool:
        """Thread-safe popularity check"""
        try:
            score = self.redis.zscore(f"{self.popularity_prefix}daily", hash_value)
            return score and score >= int(threshold)
        except Exception:
            # If Redis fails, assume not popular
            return False
    
    def cache_complete_text(self, hash_value: str, metadata: TextEntity, content: str, ttl: int = None):
        """Atomically cache both metadata and content"""
        ttl = ttl or self.default_ttl
        
        # Use Redis pipeline for atomic multi-operation
        pipe = self.redis.pipeline()
        pipe.setex(f"{self.metadata_prefix}{hash_value}", ttl, json.dumps(metadata.to_dict()))
        pipe.setex(f"{self.content_prefix}{hash_value}", ttl, content)
        pipe.execute()  # Atomic execution

    def get_complete_text(self, hash_value: str) -> dict:
        """Atomically get both metadata and content with popularity increment"""
        result = self._get_complete_text_script(
            keys=[
                f"{self.metadata_prefix}{hash_value}",
                f"{self.content_prefix}{hash_value}",
                f"{self.popularity_prefix}daily"
            ],
            args=[hash_value]
        )
        if result:
            metadata_cached, content_cached = result
            return {
                "metadata": TextEntity.from_dict(json.loads(metadata_cached)),
                "content": content_cached.decode('utf-8') if isinstance(content_cached, bytes) else content_cached
            }
        
        return None 