import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import urllib
import datetime

print("The file has loaded!")
async def start():
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
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
                try:
                    # Construct empty vCon, set meta data
                    vCon = vcon.Vcon()
                    caller = body["to_number"]
                    called = body["from_number"]
                    vCon.set_party_tel_url(caller)
                    vCon.set_party_tel_url(called)
                    adapter_meta= {}
                    adapter_meta['type'] = 'call_completed'
                    adapter_meta['adapter'] = "volie"
                    adapter_meta['received_at'] = datetime.datetime.now().isoformat()
                    adapter_meta['payload'] = body
                    vCon.attachments.append(adapter_meta)


                    vCon.attachments.append(body)
                    await r.publish("ingress-events", vCon.dumps())
                    element = await r.lpop("volie-conserver-feed") 
                except Exception as e:
                    print("volie adapter error: {}".format(e))


        except asyncio.TimeoutError:
            pass
    
        except asyncio.CancelledError:
            print("Volie Cancelled")
            break

    print("Adapter stopped")    

