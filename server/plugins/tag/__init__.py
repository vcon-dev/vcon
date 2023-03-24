from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
vcon_redis = VconRedis()
logger = init_logger(__name__)

default_options = {
    "tags": ["iron", "maiden"],
}

async def run(
    vcon_uuid,
    opts=default_options,
):
    logger.debug("Starting tag::run")
    vCon = await vcon_redis.get_vcon(vcon_uuid)
    vCon.add_analysis(0, 'tags', opts['tags'])
    await vcon_redis.store_vcon(vCon)

    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid