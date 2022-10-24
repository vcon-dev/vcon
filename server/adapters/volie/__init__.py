import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import urllib
import datetime


def create_vcon_from_phone_call(body):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        caller = body.get('caller', 'unknown')
        called = body.get('called', 'unknown')
        vCon.set_party_tel_url(caller,-1)
        vCon.set_party_tel_url(called,-1)
        return vCon

    except Exception as e:
        print(e)
        return None


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
                match body['communication_type']:
                    case 'Phone':
                        print("Found a phone call")
                        vCon = create_vcon_from_phone_call(body)
                    case "_":
                        print("Unhandled volie communication type: ", body['communication_type'])
                        continue

                adapter_meta= {}
                adapter_meta['src'] = 'conserver'
                adapter_meta['type'] = 'call_completed'
                adapter_meta['adapter'] = "volie"
                adapter_meta['received_at'] = datetime.datetime.now().isoformat()
                adapter_meta['payload'] = body
                vCon.attachments.append(adapter_meta)
                await r.publish("ingress-events", vCon.dumps())
        except asyncio.TimeoutError:
            pass    
        except asyncio.CancelledError:
            print("Volie Cancelled")
            break

    print("Volie Adapter stopped")    

