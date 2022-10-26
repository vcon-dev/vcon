import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import datetime
import asyncio
import boto3


from settings import AWS_KEY_ID, AWS_SECRET_KEY, AWS_BUCKET, DEEPGRAM_KEY, MONGODB_URL

async def reader(channel: redis.client.PubSub):
    while True:
        try:
            async with async_timeout.timeout(1):
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    print("Storage adapter received: {}".format(message))
                    vcon = json.loads(message['data'])
                    try:
                        # Save the vCon to S3
                        s3 = boto3.resource(
                        's3',
                        region_name='us-east-1',
                        aws_access_key_id=AWS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_KEY
                        )
                    
                        vconId = vcon["uuid"]
                        S3Path = "plugins/call_log/" + str(vconId) + ".vcon"
                        s3.Bucket(AWS_BUCKET).put_object(Key=S3Path, Body=json.dumps(vcon))
                    except Exception as e:
                        print("S3 adapter error: {}".format(e))
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
    print("S3 adapter stopped")