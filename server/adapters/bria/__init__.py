import async_timeout
import asyncio
from datetime import datetime
import json
import logging
import logging.config
import redis.asyncio as redis
from settings import REDIS_URL, LOG_LEVEL, ENV
from redis.commands.json.path import Path
import vcon
import dateutil


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.info('Bria adapter loading')

default_options = {
    "name": "bria",
    "ingress-list": [f"bria-conserver-feed-{ENV}"], # TODO ask Thomas: Does it use this queue name or the one from Redis? why do we have both?
    "egress-topics":["ingress-vcons"],
}


def time_diff_in_seconds(start_time: str, end_time: str) -> int:
    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    duration = end_time - start_time
    return duration.seconds


async def start(opts=default_options):
    logger.info("Starting the bria adapter")
    # Setup redis
    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    while True:
        # logger.info("Bria adaptor loop")
        try:
            async with async_timeout.timeout(10):
                for ingress_list in opts["ingress-list"]:
                    list, data = await r.blpop(ingress_list)
                    logger.info("Getting from list %s", ingress_list)
                    if data is None:
                        continue
                    payload = json.loads(data)
                    records = payload.get("Records")
                    if records:
                        logger.info("Processing s3 %s", payload)
                        first_record = records[0]
                        s3_object_key = first_record["s3"]["object"]["key"]
                        bria_call_id = s3_object_key.replace('.wav', '')
                        # lookup the vCon in redis using this ID
                        # FT.SEARCH idx:adapterIdIndex '@adapter:{bria} @id:{f8be045704cb4ea98d73f60a88590754}'
                        result = await r.ft(index_name="idx:adapterIdIndex").search("@adapter:{bria} @id:{%s}" % bria_call_id)
                        vcon_key = result.docs[0].id
                        vcon_data = json.loads(result.docs[0].json)
                        vcon_id = vcon_key[5:] # Remove the "vcon:" prefix from the keyy
                        payload = vcon_data["attachments"][0]["payload"]
                        dialog_data = {
                            "type": "recording",
                            "filename": s3_object_key,
                            "start": dateutil.parser.isoparse(payload["connectedAt"]).isoformat(),
                            "duration": time_diff_in_seconds(payload["connectedAt"], payload["endedAt"])
                        }
                        await r.json().arrinsert(vcon_key, '$.dialog', 0, dialog_data)
                        for egress_topic in opts["egress-topics"]:
                            await r.publish(egress_topic, vcon_id)
                    else:
                        logger.info("Bria adapter received")
                        body = json.loads(payload.get("Message"))
                        logger.info("Bria adapter received")
                        logger.info("Bria adapter received: %s", body)

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
                        logger.info("New vCon created: %s", vCon.uuid)
                        key = f"vcon:{vCon.uuid}"
                        cleanvCon = json.loads(vCon.dumps())
                        await r.json().set(key, Path.root_path(), cleanvCon)
                        for egress_topic in opts["egress-topics"]:
                            await r.publish(egress_topic, vCon.uuid)
        except asyncio.CancelledError:
            logger.info("Bria Cancelled")
            break
        except asyncio.TimeoutError:
            pass
        except Exception:
                logger.error("bria adaptor error:\n%s", traceback.format_exc())

    logger.info("Bria adapter stopped")