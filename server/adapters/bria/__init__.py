import async_timeout
import asyncio
from datetime import datetime
import json
import logging
import logging.config
import redis.asyncio as redis
from settings import REDIS_URL
import vcon

logger = logging.getLogger(__name__)
logger.info('Bria adapter loading')

default_options = {
    "name": "bria",
    "ingress-list": ["bria-conserver-feed"],
    "egress-topics":["ingress-vcons"],
}

async def start(opts=default_options):
    logger.info("Starting the bria adapter")
    # Setup redis
    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    while True:
        try:
            async with async_timeout.timeout(10):
                for ingress_list in opts["ingress-list"]:
                    list, data = await r.blpop(ingress_list)
                    if data is None:
                        continue

                    try:
                        list = list.decode('utf-8')
                        payload = json.loads(data.decode('utf-8'))
                        message = json.loads(payload.get("Message"))
                        body = json.loads(message['default']['body'])
                        logger.info("Bria adapter received")
                        print("Bria adapter received: {}".format(body))

                        # Construct empty vCon, set meta data
                        vCon = vcon.Vcon()
                        vCon.set_party_tel_url(body["to_number"])
                        vCon.set_party_tel_url(body["from_number"])

                        # Set the adapter meta so we know where the this came from
                        adapter_meta= {
                            "adapter": "bria",
                            "adapter_version": "0.1.0",
                            "src": ingress_list,
                            "type": 'call_history',
                            "received_at": datetime.now().isoformat(),
                            "payload": body
                        }
                        vCon.attachments.append(adapter_meta)

                        # Publish the vCon
                        logger.info("New vCon created: {}".format(vCon.uuid))
                        key = "vcon-{}".format(vCon.uuid)
                        await r.json().set(key, Path.root_path(), vCon)
                        for egress_topic in opts["egress-topics"]:
                            await r.publish(egress_topic, vCon.uuid)
                    except Exception as e:
                        logger.error("bria adapter error: {}".format(e))


        except asyncio.CancelledError:
            logger.info("Bria Cancelled")
            break

        except asyncio.TimeoutError:
            pass

    logger.info("Bria dapter stopped")    
