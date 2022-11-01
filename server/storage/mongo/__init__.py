import asyncio
import redis.asyncio as redis
import json
import asyncio
import pymongo
from settings import MONGODB_URL
import logging

logger = logging.getLogger(__name__)
default_options = {
    "name": "call_log",
    "ingress-topics": ["ingress-vcons"],
    "transcribe": True,
    "min_transcription_length": 10,
    "deepgram": False,
    "egress-topics":[],
}
options = {}

async def start(opts=default_options):
    logger.info("Starting the call_log plugin")

    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        m = pymongo.MongoClient(MONGODB_URL)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data'].decode('utf-8')
                    logger.info("mongo plugin: received vCon: {}".format(vConUuid))
                    body = await r.get("vcon-{}".format(str(vConUuid)))
                    vCon = json.loads(body)
                    m.conserver.call_log.insert_one(vCon)
                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("mongo plugin: error: {}".format(e))


    except asyncio.CancelledError:
        logger.debug("call log plugin Cancelled")

    logger.info("call log plugin stopped")    



