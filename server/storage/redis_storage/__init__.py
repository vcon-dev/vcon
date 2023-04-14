import redis.asyncio as redis
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
logger = init_logger(__name__)


default_options = {
                    "name": "redis_storage",
                    "redis_url":"redis://:localhost:6379",
                    "prefix":"vcon_storage",
                    "expires": 60*60*24*7
                }
async def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the REDIS storage")
    try:
        # Cannot reate redis clients in global context as they get started on async event
        # loop which may go away.
        vcon_redis = VconRedis()
        vcon = await vcon_redis.get_vcon(vcon_uuid)
        r = redis.Redis.from_url(opts['redis_url'])
        await r.set(f"{opts['prefix']}:{vcon_uuid}", vcon.dumps(), ex=opts['expires'])
        logger.info(f"redis storage plugin: inserted vCon: {vcon_uuid}")
    except Exception as e:
        logger.error(f"redis storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ")
        raise e

