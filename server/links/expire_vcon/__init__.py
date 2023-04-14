import asyncio
from lib.logging_utils import init_logger
import copy
import traceback
from lib.sentry import init_sentry
from datetime import timedelta
import server.redis_mgr

init_sentry()


logger = init_logger(__name__)

default_options = {
    "name": "expire_vcon",
    "ingress-topics": [],
    "egress-topics": [],
}


async def start(opts=None):
    if opts is None:
        opts = copy.deepcopy(default_options)
    logger.info("Starting the expire_vcon plugin")
    while True:
        try:
            r = server.redis_mgr.get_client()
            p = r.pubsub(ignore_subscribe_messages=True)
            await p.subscribe(*opts["ingress-topics"])
            async for message in p.listen():
                vConUuid = message["data"]
                logger.info(f"expire_vcon plugin: received vCon: {vConUuid}")
                await r.expire(f"vcon:{vConUuid}", timedelta(days=1))
                logger.info(f"expire_vcon plugin: set expire for {vConUuid}")
                for topic in opts["egress-topics"]:
                    await r.publish(topic, vConUuid)
        except asyncio.CancelledError:
            logger.debug("expire_vcon Cancelled")
            break
        except Exception:
            logger.error("expire_vcon plugin: error: \n%s", traceback.format_exc())
            logger.error("Shoot!")
    logger.info("expire_vcon stopped")

