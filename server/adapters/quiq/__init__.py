import asyncio
import async_timeout
import redis.asyncio as redis
import json
import vcon
import datetime
import logging

logger = logging.getLogger(__name__)

async def start():
    logger.info("Starting the quiq adapter")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(10):
                list, data = await r.blpop("quiq-conserver-feed")
                if data is None:
                    continue

                list = list.decode()
                payload = json.loads(data.decode())
                body = payload.get("default")
                                
                # Construct empty vCon, set meta data
                vCon = vcon.Vcon()
                vCon.set_uuid("vcon.dev")
                caller = body["src"]
                called = body["dst"]
                vCon.set_party_parameter("tel", caller)
                vCon.set_party_parameter("tel", called)

                # Set the adapter meta so we know where this thing came from
                adapter_meta= {}
                adapter_meta['src'] = 'conserver'
                adapter_meta['type'] = 'chat_completed'
                adapter_meta['adapter'] = "quiq"
                adapter_meta['received_at'] = datetime.datetime.now().isoformat()
                adapter_meta['payload'] = body
                vCon.attachments.append(adapter_meta)
                
                # Publish the vCon
                logger.info("New vCon created: {}".format(vCon.uuid))
                await r.set("vcon-{}".format(vCon.uuid), vCon.dumps())
                await r.publish("ingress-vcons", str(vCon.uuid))
                await asyncio.sleep(1)

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            logger.debug("quiq Cancelled")
            break

        except Exception as e:
            logger.debug("quiq adapter error: {}".format(e))

    logger.info("Quiq adapter stopped")    



