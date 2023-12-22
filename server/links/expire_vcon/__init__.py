import redis_mgr
from lib.logging_utils import init_logger

logger = init_logger(__name__)

default_options = {"seconds": 60 * 60 * 24}


async def run(vcon_uuid, link_name, opts=default_options):
    logger.debug("Starting expire_vcon::run")
    r = redis_mgr.get_client()
    await r.expire(f"vcon:{vcon_uuid}", opts["seconds"])
    logger.info(f"expire_vcon plugin: set expire for {vcon_uuid}")
    return vcon_uuid
