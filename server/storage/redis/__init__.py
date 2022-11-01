import asyncio
import async_timeout
import redis.asyncio as redis
import json
import asyncio
import logging

logger = logging.getLogger(__name__)
default_options = {
    "name": "redis",
    "ingress-topics": ["ingress-vcons"],
    "egress-topics":[],
    "redis-set-name": "call_log"
}
options = {}

async def start(opts=default_options):
    logger.info("Starting the call_log plugin")

    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data'].decode('utf-8')
                    logger.info("Redis received vCon: {}".format(vConUuid))
                    # Save this vCon into Redis set.
                    await redis.sadd(opts["redis-set-name"], vConUuid)
                await asyncio.sleep(0.01)

            except Exception as e:
                print("REDIS adapter error: {}".format(e))

    except asyncio.CancelledError:
        logger.debug("Redis storage adapter Cancelled")

    logger.info("Redis storage adapter stopped")    