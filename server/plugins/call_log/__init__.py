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


async def save_to_s3(vcon):
    json_string = vcon.dumps()
    # Save the vCon to S3
    s3 = boto3.resource(
    's3',
    region_name='us-east-1',
    aws_access_key_id=AWS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY
    )
 
    vconId = vcon.uuid
    S3Path = "plugins/call_log/" + str(vconId) + ".vcon"
    s3.Bucket(AWS_BUCKET).put_object(Key=S3Path, Body=json_string)

async def save_to_redis(vcon, redis_client):
    json_string = vcon.dumps()
    # Save the vCon to Redis (for now)
    await redis_client.sadd("call_log", json_string)

async def save_to_mongo(vcon, mongo_client):
    json_string = vcon.dumps()
    json_vcon = json.loads(json_string)
    mongo_client.conserver.call_log.insert_one(json_vcon)
    

async def manage_ended_call(inbound_vcon, redis_client, mongo_client):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        vCon.loads(json.dumps(inbound_vcon))

        # Add that this plugin has processed this vCon
        vCon.attachments.append({"plugin": "call_log"})
        # Save the vCon to the database(s)
        await save_to_s3(vCon)
        await save_to_redis(vCon, redis_client)
        await save_to_mongo(vCon, mongo_client)
    
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
                await pubsub.subscribe("ingress-events")
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



