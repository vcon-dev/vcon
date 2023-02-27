import asyncio

import pymongo
import redis.asyncio as redis
from lib.logging_utils import init_logger
from redis.commands.json.path import Path
from settings import MONGODB_URL, REDIS_URL
from datetime import datetime

logger = init_logger(__name__)

m = pymongo.MongoClient(MONGODB_URL)

default_options = {"name": "mongo", "ingress-topics": [], "egress-topics": []}
options = {}


def prepare_vcon_for_mongo(vcon: dict) -> dict:
    vcon["_id"] = vcon["uuid"]
    vcon["created_at"] = datetime.fromisoformat(vcon["created_at"])
    for dialog in vcon["dialog"]:
        dialog["start"] = datetime.fromisoformat(dialog["start"])
    return vcon


async def start(opts=default_options):
    logger.info("Starting the mongo plugin")
    try:
        r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts["ingress-topics"])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vcon_uuid = message["data"]
                    logger.info(
                        "mongo storage plugin: received vCon: {}".format(vcon_uuid)
                    )
                    inbound_vcon = await r.json().get(
                        f"vcon:{str(vcon_uuid)}", Path.root_path()
                    )
                    results = m.conserver.vcon.insert_one(
                        prepare_vcon_for_mongo(inbound_vcon)
                    )

                    logger.info(
                        f"mongo storage plugin: inserted vCon: {vcon_uuid}, results: {results} "
                    )
                    for topic in opts["egress-topics"]:
                        await r.publish(topic, vcon_uuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("mongo storage: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("mongo storage Cancelled")

    logger.info("mongo storage stopped")
