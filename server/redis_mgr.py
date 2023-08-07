""" 
Package to manage Redis connection pool and clients

Setup of redis clients cannot be done globally in each module as it will 
bind to a asyncio loop which may be started and stopped.  In which case
redis will be bound to an old loop which will no longer work

The redis connection pool must be shutdown and restarted when FASTApi does.
"""

from lib.logging_utils import init_logger
import redis.asyncio.connection
import redis.asyncio.client
from settings import REDIS_URL



logger = init_logger(__name__)

REDIS_POOL = None
REDIS_POOL_INITIALIZATION_COUNT = 0


def create_pool():
    global REDIS_POOL
    global REDIS_POOL_INITIALIZATION_COUNT
    if REDIS_POOL is not None:
        logger.info("Redis pool already created")
    else:
        logger.info("Creating Redis pool...")
        REDIS_POOL_INITIALIZATION_COUNT += 1
        REDIS_POOL = redis.asyncio.connection.ConnectionPool.from_url(REDIS_URL)
        logger.info(
            "Redis pool created. redis connection: host: {} port: {} max connections: {} initialization count: {}".format(
                REDIS_POOL.connection_kwargs.get("host", "None"),
                REDIS_POOL.connection_kwargs.get("port", "None"),
                REDIS_POOL.max_connections,
                REDIS_POOL_INITIALIZATION_COUNT,
            )
        )

    #logger.debug(dir(REDIS_POOL))


async def shutdown_pool():
    global REDIS_POOL
    if REDIS_POOL is not None:
        logger.info("disconnecting Redis pool")
        log_pool_stats()
        tmp_pool = REDIS_POOL
        REDIS_POOL = None
        await tmp_pool.disconnect(inuse_connections=True)
        logger.info("Redis pool shutdown")

    else:
        logger.info("Redis pool already disconnected")


def log_pool_stats():
  if(REDIS_POOL):
    logger.info("redis pool max: {} in use: {}  available: {}".format(REDIS_POOL.max_connections, len(REDIS_POOL._in_use_connections), len(REDIS_POOL._available_connections)))
  else:
    logger.info("no active redis pool")

def get_client():
    logger.debug("entering get_client")
    global REDIS_POOL
    if REDIS_POOL is None:
        logger.info("REDIS_POOL is not initialized")
        create_pool()
        #create_pool()
    r = redis.asyncio.client.Redis(connection_pool=REDIS_POOL)
    logger.debug("client type: {}".format(type(r)))
    return r

async def set_key(key, value):
    r = get_client()
    result = await r.json().set(key, "$", value)
    return result

async def get_key(key):
    r = get_client()
    result = await r.json().get(key)
    return result

async def delete_key(key):
    r = get_client()
    result = await r.delete(key)
    return result

async def show_keys(pattern):
    r = get_client()
    result = await r.keys(pattern)
    return result