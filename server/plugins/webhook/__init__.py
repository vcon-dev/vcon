import asyncio

import aiohttp
import redis.asyncio as redis
import simplejson as json
from lib.logging_utils import init_logger
from redis.commands.json.path import Path

import vcon

logger = init_logger(__name__)

r = redis.Redis(host="localhost", port=6379, db=0)

default_options = {
    "name": "webhook",
    "ingress-topics": ["test-sentiment"],
    "egress-topics": [],
    "webhook-urls": ["https://eo91qivu6evxsty.m.pipedream.net"],
}
options = {}


async def run(
    vcon_uuid,
    opts=default_options,
):
    inbound_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())
    vCon = vcon.Vcon()
    vCon.loads(json.dumps(inbound_vcon))
    # Post this to each webhook url
    for url in opts["webhook-urls"]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=inbound_vcon) as resp:
                logger.info("webhook plugin: posted to webhook url: {}".format(url))
                logger.info("webhook plugin: response: {}".format(resp.status))


async def start(opts=default_options):
    logger.info("Starting the webhook plugin")
    try:
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts["ingress-topics"])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message["data"].decode("utf-8")
                    logger.info("webhook plugin: received vCon: {}".format(vConUuid))
                    await run(vConUuid, opts)
                    for topic in opts["egress-topics"]:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("webhook plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("webhook Cancelled")

    logger.info("webhook stopped")
