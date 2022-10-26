import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import urllib
import datetime

async def start():
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(1):
                element = await r.lpop("bria-conserver-feed")
                if element is None:
                    await asyncio.sleep(1)
                    continue
                decoded_element = json.loads(element)
                message = json.loads(decoded_element.get("Message"))
                body = json.loads(message['default']['body'])
                print("Bria adapter received: {}".format(body))
                try:
                    # Construct empty vCon, set meta data
                    vCon = vcon.Vcon()
                    vCon.set_uuid("vcon.dev")
                    caller = body["to_number"]
                    called = body["from_number"]
                    vCon.set_party_tel_url(caller)
                    vCon.set_party_tel_url(called)
                    adapter_meta= {}
                    adapter_meta['src'] = 'conserver'
                    adapter_meta['type'] = 'call_history'
                    adapter_meta['adapter'] = "bria"
                    adapter_meta['received_at'] = datetime.datetime.now().isoformat()
                    adapter_meta['payload'] = body
                    vCon.attachments.append(adapter_meta)


                    vCon.attachments.append(body)
                    await r.publish("ingress-vcons", vCon.dumps())
                except Exception as e:
                    print("bria adapter error: {}".format(e))


        except asyncio.TimeoutError:
            pass
    
        except asyncio.CancelledError:
            print("Volie Cancelled")
            break

    print("Adapter stopped")    




























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
                await r.publish("ingress-vcons", json.dumps(msg))

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            print("Bria Cancelled")
            break

    print("Adapter stopped")    



