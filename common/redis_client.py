import redis
from django.conf import settings

# Establish a connection pool
# A connection pool reuses open connections insteasd of closing and openting them on every request
redis_client = redis.Redis(
    host=getattr(settings, 'REDIS_HOST', 'localhost'),
    port=getattr(settings, 'REDIS_PORT', 6379),
    db =0,
    decode_responses=True # <- CRITICAL: This automatically converts binary data into standard Python string
)