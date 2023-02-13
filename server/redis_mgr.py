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

import traceback
import sys

logger = init_logger(__name__)

REDIS_POOL = None
REDIS_POOL_INITIALIZATION_COUNT = 0

def create_pool():
  global REDIS_POOL
  global REDIS_POOL_INITIALIZATION_COUNT
  if(REDIS_POOL is not None):
    logger.info("Redis pool already created")
  else:
    REDIS_POOL_INITIALIZATION_COUNT += 1
    REDIS_POOL = redis.asyncio.connection.ConnectionPool.from_url(REDIS_URL)
    logger.info('redis connection: host: {} port: {} max connections: {} initialization count: {}'.format(
      REDIS_POOL.connection_kwargs.get("host", "None"),
      REDIS_POOL.connection_kwargs.get("port", "None"),
      REDIS_POOL.max_connections,
      REDIS_POOL_INITIALIZATION_COUNT))

  logger.debug(dir(REDIS_POOL))

async def shutdown_pool():
  global REDIS_POOL
  if(REDIS_POOL is not None):
    logger.info("disconnecting Redis pool")
    tmp_pool = REDIS_POOL
    REDIS_POOL = None
    await tmp_pool.disconnect(inuse_connections=True)

  else:
    logger.info("Redis pool already disconnected")

def get_client():
  global REDIS_POOL
  if(REDIS_POOL is None):
    #traceback.print_exc()
    print("Error: redis pool not initialized", file=sys.stdout)
    traceback.print_stack(file=sys.stdout)
    logger.info("redis connection pool not initialized")
    e = Exception("Redis pool not initialized")
    raise e

  logger.info("getting redis connection")
  r = redis.asyncio.client.Redis(connection_pool=REDIS_POOL)
  #r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

  return(r)

