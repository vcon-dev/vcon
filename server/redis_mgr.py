""" 
Package to manage Redis connection pool and clients

Setup of redis clients cannot be done globally in each module as it will 
bind to a asyncio loop which may be started and stopped.  In which case
redis will be bound to an old loop which will no longer work

The redis connection pool must be shutdown and restarted when FASTApi does.
"""

from lib.logging_utils import init_logger
from redis import Redis
from redis.asyncio import Redis as RedisAsync
# from redis.asyncio.connection import ConnectionPool
# from redis.asyncio.client import Redis
from settings import REDIS_URL

logger = init_logger(__name__)

redis_async = RedisAsync.from_url(REDIS_URL, decode_responses=True)
redis = Redis.from_url(REDIS_URL, decode_responses=True)


def get_client():
    return redis


def set_key(key, value):
    result = redis.json().set(key, "$", value)
    return result


def get_key(key):
    result = redis.json().get(key)
    return result


def delete_key(key):
    result = redis.delete(key)
    return result


def show_keys(pattern):
    result = r.keys(pattern)
    return result