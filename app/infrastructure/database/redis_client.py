import redis
import os
from redis_om import get_redis_connection

# Create Redis client
def get_redis_client():
    redis_client = get_redis_connection(
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=int(os.environ.get('REDIS_PORT', '6379')),
        password=os.environ.get('REDIS_PASSWORD', None),
        decode_responses=True
    )
    try:
        yield redis_client
    finally:
        redis_client.close()
