import os , redis
from redis.commands.json.path import Path
from datetime import datetime, timedelta , timezone

_REDIS_HOST = os.getenv('REDIS_HOST', 'redis-18473.c264.ap-south-1-1.ec2.redns.redis-cloud.com')
_REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'OH3cffZ7CzaAJXgxfwOlkZQxAIIAIRJK')
_REDIS_PORT = os.getenv('REDIS_PORT', 18473)
_REDIS_EXPIRE_TIME = datetime.now(timezone.utc) + timedelta(seconds=60)

_cache = redis.Redis(
  host=_REDIS_HOST,
  port=_REDIS_PORT,
  password=_REDIS_PASSWORD)

def cache_get(key):
    return _cache.json().get(key)

def cache_set(key, value):
    _cache.json().set(key, Path.root_path() , value)
    _cache.expireat(key, _REDIS_EXPIRE_TIME)

def cache_exists(key):
    return len(_cache.json().objkeys(key) or []) > 0

def get_redis_connection_url():
    return f'redis://:{_REDIS_PASSWORD}@{_REDIS_HOST}:{_REDIS_PORT}/0'