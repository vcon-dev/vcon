from datetime import date
from pydoc import doc
from urllib.parse import urlparse
import async_timeout
import asyncio
import datetime
import json
import logging
import redis.asyncio as redis
import vcon

logger = logging.getLogger(__name__)

async def start():
    logger.info("Starting the bria adapter")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(10):
                list, data = await r.blpop("bria-conserver-feed")
                if data is None:
                    continue

                try:
                    list = list.decode()
                    payload = json.loads(data.decode())
                    message = json.loads(payload.get("Message"))
                    body = json.loads(message['default']['body'])
                    print("Bria adapter received: {}".format(body))

                    # Construct empty vCon, set meta data
                    vCon = vcon.Vcon()
                    vCon.set_uuid("vcon.dev")
                    caller = body["to_number"]
                    called = body["from_number"]
                    vCon.set_party_tel_url(caller)
                    vCon.set_party_tel_url(called)

                    # Set the adapter meta so we know where the this came from
                    adapter_meta= {}
                    adapter_meta['src'] = 'conserver'
                    adapter_meta['type'] = 'call_history'
                    adapter_meta['adapter'] = "bria"
                    adapter_meta['received_at'] = datetime.datetime.now().isoformat()
                    adapter_meta['payload'] = body
                    vCon.attachments.append(adapter_meta)

                    # Publish the vCon
                    logger.info("New vCon created: {}".format(vCon.uuid))
                    await r.set("vcon-{}".format(vCon.uuid), vCon.dumps())
                    await r.publish("ingress-vcons", str(vCon.uuid))
                except Exception as e:
                    print("bria adapter error: {}".format(e))


        except asyncio.CancelledError:
            print("Bria Cancelled")
            break

        except asyncio.TimeoutError:
            pass
    

    print("Bria dapter stopped")    
