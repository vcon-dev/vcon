from redis_mgr import redis
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger

logger = init_logger(__name__)


default_options = {
    "redis_url": "redis://:localhost:6379",
    "prefix": "vcon_storage",
    "expires": 60 * 60 * 24 * 7,
}


def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the REDIS storage")
    try:
        vcon_redis = VconRedis()
        vcon = vcon_redis.get_vcon(vcon_uuid)
        redis.set(f"{opts['prefix']}:{vcon_uuid}", vcon.dumps(), ex=opts["expires"])
        logger.info(f"redis storage plugin: inserted vCon: {vcon_uuid}")
    except Exception as e:
        logger.error(
            f"redis storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} "
        )
        raise e
