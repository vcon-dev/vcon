import async_timeout
import asyncio
from datetime import datetime
import json
import logging
import logging.config
import redis.asyncio as redis
from settings import REDIS_URL, LOG_LEVEL
from redis.commands.json.path import Path
import vcon


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
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
                        payload = json.loads(data)
                        body = json.loads(payload.get("Message"))
                        logger.info("Bria adapter received")
                        print("Bria adapter received: {}".format(body))

                        # Construct empty vCon, set meta data
                        vCon = vcon.Vcon()
                        email = body.get("email")
                        username = email.split('@')[0]
                        first_name = username.split('.')[0]
                        last_name = username.split('.')[1]
                        full_name = first_name + " " + last_name
                        if body.get("direction") == "out":
                            src = body.get("extension")
                            dst = body.get("customerNumber")
                            email = body.get("email")
                            vCon.set_party_parameter("tel", src, -1)
                            vCon.set_party_parameter("mailto", email, 0)
                            vCon.set_party_parameter("name", full_name, 0)
                            vCon.set_party_parameter("tel", dst, -1)

                        else:
                            dst = body.get("extension")
                            src = body.get("customerNumber")
                            vCon.set_party_parameter("tel", src, -1)
                            vCon.set_party_parameter("mailto", email, -1)
                            vCon.set_party_parameter("name", full_name, 1)
                            vCon.set_party_parameter("tel", dst, 1)

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
                        key = "vcon:{}".format(vCon.uuid)
                        cleanvCon = json.loads(vCon.dumps())
                        await r.json().set(key, Path.root_path(), cleanvCon)
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
