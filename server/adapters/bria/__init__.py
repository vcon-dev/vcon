import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json


async def start():
    print("Starting the Bria adapter")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(5):
                list, data = await r.blpop("bria-conserver-feed")
                if data is None:
                    await asyncio.sleep(1)
                    continue
                list = list.decode()
                payload = json.loads(data.decode())
                msg = {}
                original_msg = json.loads(payload.get("Message"))
                msg['type'] = original_msg['status']["@type"]
                msg['source'] = "bria"       
                msg['payload'] = original_msg
                # await r.publish("ingress-events", json.dumps(msg))

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            print("Bria Cancelled")
            break

    print("Adapter stopped")    



