from lib.logging_utils import init_logger
import redis.asyncio as redis
from redis.commands.json.path import Path
import asyncio
import asyncio
import redis.asyncio as redis
import pymongo
from settings import MONGODB_URL

logger = init_logger(__name__)

r = redis.Redis(host="localhost", port=6379, db=0)
m = pymongo.MongoClient(MONGODB_URL)

default_options = {"name": "mongo", "ingress-topics": [], "egress-topics": []}
options = {}


async def run(
    vcon_uuid,
    opts=default_options,
):
    inbound_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())
    inbound_vcon["_id"] = vcon_uuid
    results = m.conserver.vcon.insert_one(inbound_vcon)
    logger.info(
        f"mongo storage plugin: inserted vCon: {vcon_uuid}, results: {results} "
    )


async def start(opts=default_options):
    logger.info("Starting the mongo plugin")
    try:
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts["ingress-topics"])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message["data"].decode("utf-8")
                    logger.info(
                        "mongo storage plugin: received vCon: {}".format(vConUuid)
                    )
                    await run(vConUuid, opts)
                    for topic in opts["egress-topics"]:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("mongo storage: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("mongo storage Cancelled")

    logger.info("mongo storage stopped")
