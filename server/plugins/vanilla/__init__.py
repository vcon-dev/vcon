import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import asyncio
import boto3
from settings import AWS_KEY_ID, AWS_SECRET_KEY, AWS_BUCKET, DEEPGRAM_KEY, MONGODB_URL


async def manage_ended_call(inbound_vcon, redis_client):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        vCon.loads(json.dumps(inbound_vcon))

        # Add that this plugin has processed this vCon
        vCon.attachments.append({"plugin": "vanilla"})

        # Save the vCon to the database
        json_string = vCon.dumps()
        # Save the vCon to S3
        s3 = boto3.resource(
        's3',
        region_name='us-east-1',
        aws_access_key_id=AWS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_KEY
        )
        S3Path = "plugins/vanilla/" + str(inbound_vcon["_id"]) + ".vcon"
        s3.Bucket(AWS_BUCKET).put_object(Key=S3Path, Body=json_string)

        # Save the vCon to Redis (for now)
        await redis_client.sadd("vanilla", json_string)
    
    except Exception as e:
        print("manage_ended_call error: {}".format(e))

async def start():
    print("Starting the vanilla plugin")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(5):
                pubsub = r.pubsub()
                await pubsub.subscribe("ingress-events")
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        body = json.loads(message['data'].decode())
                        await manage_ended_call(body, r)
                        await asyncio.sleep(1)

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            print("vanilla plugin Cancelled")
            break

    print("vanilla plugin stopped")    



