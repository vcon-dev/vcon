import asyncio
import redis.asyncio as redis
from lib.logging_utils import init_logger
from settings import REDIS_URL
import copy
from lib.sentry import init_sentry
from datetime import timedelta

init_sentry()

r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

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
    try:
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts["ingress-topics"])
        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message["data"]
                    logger.info(f"expire_vcon plugin: received vCon: {vConUuid}")
                    await r.expire(f"vcon:{vConUuid}", timedelta(days=1))
                    logger.info(f"expire_vcon plugin: set expire for {vConUuid}")
                    for topic in opts["egress-topics"]:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("expire_vcon plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("expire_vcon Cancelled")

    logger.info("expire_vcon stopped")
