import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import asyncio
import boto3
import pymongo
from settings import AWS_KEY_ID, AWS_SECRET_KEY, AWS_BUCKET, DEEPGRAM_KEY, MONGODB_URL

async def manage_ended_call(inbound_vcon, redis_client, mongo_client):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        vCon.loads(json.dumps(inbound_vcon))

        # Add that this plugin has processed this vCon
        vCon.attachments.append({"plugin": "call_log"})

        # Send this out to the storage adapters
        await redis_client.publish("storage-events", vCon.dumps())
    
    except Exception as e:
        print("call_log error: {}".format(e))

async def start():
    print("Starting the call_log plugin")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    m = pymongo.MongoClient(MONGODB_URL)

    while True:
        try:
            async with async_timeout.timeout(5):
                pubsub = r.pubsub()
                await pubsub.subscribe("ingress-vcons")
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        body = json.loads(message['data'].decode())
                        await manage_ended_call(body, r, m)
                        await asyncio.sleep(1)

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            print("call log plugin Cancelled")
            break

    print("call log plugin stopped")    



