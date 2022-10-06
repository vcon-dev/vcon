import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import urllib
import datetime


async def start():
    print("Starting the quiq adapter")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(5):
                list, data = await r.blpop("quiq-conserver-feed")
                if data is None:
                    await asyncio.sleep(1)
                    continue
                list = list.decode()
                payload = json.loads(data.decode())
                body = payload.get("default")
                                
                # Construct empty vCon, set meta data
                vCon = vcon.Vcon()
                caller = body["src"]
                called = body["dst"]
                vCon.set_party_tel_url(caller)
                vCon.set_party_tel_url(called)
                vCon.attachments.append(body)
                await r.publish("ingress-events", vCon.dumps())
                await asyncio.sleep(1)

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            print("quiq Cancelled")
            break

        except Exception as e:
            print("quiq adapter error: {}".format(e))

    print("Adapter stopped")    



