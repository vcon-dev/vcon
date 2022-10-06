import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json


print("The file has loaded!")
async def start():
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    print("Starting volie adapter", r)
    while True:
        try:
            async with async_timeout.timeout(1):
                element = await r.lpop("volie-conserver-feed")
                if element is None:
                    await asyncio.sleep(1)
                    continue
                decoded_element = json.loads(element)
                message = json.loads(decoded_element.get("Message"))
                body = json.loads(message['default']['body'])
                msg = {}
                msg['source'] = "volie"       
                msg['type'] = "call_completed"
                msg['payload'] = body
                print("Message to publish: ", msg)         
                await r.publish("ingress-events", json.dumps(msg))
                element = await r.lpop("volie-conserver-feed")                        
        except asyncio.TimeoutError:
            pass
    
        except asyncio.CancelledError:
            print("Volie Cancelled")
            break

    print("Adapter stopped")    

