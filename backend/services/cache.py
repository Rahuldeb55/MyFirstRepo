"""
Cache Service — Redis-backed caching for live dashboard.
Falls back gracefully to direct DB queries when Redis is unavailable.
"""
import json
from typing import Optional

# Try to import Redis; if unavailable, use a simple in-memory fallback
try:
    import redis
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False
    redis_client = None

# In-memory fallback cache
_memory_cache: dict = {}


def cache_set(key: str, value: dict, ttl: int = 30):
    """Set a cache value with TTL (in seconds)."""
    if REDIS_AVAILABLE:
        redis_client.setex(key, ttl, json.dumps(value))
    else:
        _memory_cache[key] = value


def cache_get(key: str) -> Optional[dict]:
    """Get a cached value. Returns None if expired or missing."""
    if REDIS_AVAILABLE:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    return _memory_cache.get(key)


def cache_delete(key: str):
    """Delete a cached key."""
    if REDIS_AVAILABLE:
        redis_client.delete(key)
    else:
        _memory_cache.pop(key, None)


def invalidate_census():
    """Invalidate the census cache after a scan event."""
    cache_delete("census:live")
    cache_delete("dashboard:stats")


# --- Live Census Helpers ---

def add_student_out(roll_no: str, student_data: dict):
    """Add student to the 'currently out' set in Redis."""
    if REDIS_AVAILABLE:
        redis_client.hset("students:out", roll_no, json.dumps(student_data))
    invalidate_census()


def remove_student_out(roll_no: str):
    """Remove student from the 'currently out' set in Redis."""
    if REDIS_AVAILABLE:
        redis_client.hdel("students:out", roll_no)
    invalidate_census()


def get_students_out() -> dict:
    """Get all students currently out from Redis."""
    if REDIS_AVAILABLE:
        data = redis_client.hgetall("students:out")
        return {k: json.loads(v) for k, v in data.items()}
    return {}
