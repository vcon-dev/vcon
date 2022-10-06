import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import urllib
import datetime


async def start():
    print("Starting the ringplan adapter")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(5):
                list, data = await r.blpop("ringplan-conserver-feed")
                if data is None:
                    await asyncio.sleep(1)
                    continue

                list = list.decode()
                payload = json.loads(data.decode())
                msg = {}
                original_msg = json.loads(payload.get("Message"))
                msg['type'] = 'call_completed'
                msg['source'] = "ringplan"       
                msg['payload'] = original_msg

                # Construct empty vCon, set meta data
                vCon = vcon.Vcon()
                caller = original_msg["payload"]["cdr"]["src"]
                called = original_msg["payload"]["cdr"]["dst"]
                vCon.set_party_tel_url(caller)
                vCon.set_party_tel_url(called)

                # Save the original RingPlan JSON in the vCon
                vCon.attachments.append(original_msg)
                await r.publish("ingress-events",  vCon.dumps())

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            print("ringplan Cancelled")
            break

    print("Adapter stopped")    



