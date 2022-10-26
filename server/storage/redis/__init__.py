import asyncio
import async_timeout
import redis.asyncio as redis
import json
import asyncio

async def reader(redis: redis, channel: redis.client.PubSub):
    while True:
        try:
            async with async_timeout.timeout(1):
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    print("Storage adapter received: {}".format(message))
                    vcon = json.loads(message['data'])
                    try:
                        json_string = json.dumps(vcon)
                        # Save the vCon to Redis (for now)
                        await redis.sadd("call_log", json_string)

                    except Exception as e:
                        print("REDIS adapter error: {}".format(e))
                await asyncio.sleep(0.01)
        except asyncio.TimeoutError:
            pass


async def start():
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    pubsub =  r.pubsub()
    await pubsub.subscribe('storage-events')
    future = asyncio.create_task(reader(r, pubsub))
    await future
    print("REDIS adapter stopped")