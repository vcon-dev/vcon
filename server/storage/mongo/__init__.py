import asyncio
import async_timeout
import redis.asyncio as redis
import json
import asyncio
import pymongo
from settings import MONGODB_URL
import logging

logger = logging.getLogger(__name__)


async def reader(channel: redis.client.PubSub):
    m = pymongo.MongoClient(MONGODB_URL)

    while True:
        try:
            async with async_timeout.timeout(1):
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    vcon = json.loads(message['data'])
                    logger.info("Storage adapter received vCon: {}".format(vcon.get('uuid')))
                    try:
                        # Save the vCon to Mongo
                        m.conserver.call_log.insert_one(vcon)
                    except Exception as e:
                        print("Mongo adapter error: {}".format(e))
                await asyncio.sleep(0.01)
        except asyncio.TimeoutError:
            pass


async def start():
    # Setup redis
    logger.info("Starting the mongo storage adapter")
    r = redis.Redis(host='localhost', port=6379, db=0)
    pubsub =  r.pubsub()
    await pubsub.subscribe('storage-events')
    future = asyncio.create_task(reader(pubsub))
    await future
    logger.info("Mongo adapter stopped")
