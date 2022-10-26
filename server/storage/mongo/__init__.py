import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import datetime
import asyncio
import boto3
import pymongo
from settings import AWS_KEY_ID, AWS_SECRET_KEY, AWS_BUCKET, DEEPGRAM_KEY, MONGODB_URL

async def reader(channel: redis.client.PubSub):
    m = pymongo.MongoClient(MONGODB_URL)

    while True:
        try:
            async with async_timeout.timeout(1):
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    print("Storage adapter received: {}".format(message))
                    vcon = json.loads(message['data'])
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
    r = redis.Redis(host='localhost', port=6379, db=0)
    pubsub =  r.pubsub()
    await pubsub.subscribe('storage-events')
    future = asyncio.create_task(reader(pubsub))
    await future
    print("Mongo adapter stopped")
