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
from dateutil.parser import parse
import traceback
import phonenumbers
from typing import Optional


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.info('Bria adapter loading')

default_options = {
    "name": "bria",
    "ingress-list": [f"bria-conserver-feed-{ENV}", "bria-conserver-feed"], # TODO ask Thomas: Does it use this queue name or the one from Redis? why do we have both?
    "egress-topics":["ingress-vcons"],
}


def time_diff_in_seconds(start_time: str, end_time: str) -> int:
    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    duration = end_time - start_time
    return duration.seconds


async def handle_bria_s3_recording_event(record, opts, r):
    logger.info("Processing s3 %s", record)
    s3_object_key = record["s3"]["object"]["key"]
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


async def handle_bria_call_ended_event(body, opts, r):
    logger.info("Bria adapter received: %s", body)

    # Construct empty vCon, set meta data
    vCon = vcon.Vcon()
    email = body.get("email")
    username = email.split('@')[0]
    first_name = username.split('.')[0]
    last_name = username.split('.')[1]
    full_name = first_name + " " + last_name

    start_time = body['startedAt']
    end_time = body['endedAt']
    duration = time_diff_in_seconds(start_time, end_time)
    dealer_did = get_e164_number(body.get("dialerId"))
    customerNumber = get_e164_number(body.get("customerNumber"))
    extension = body.get("extension")

    if body.get("direction") == "out":
        email = body.get("email")
        vCon.set_party_parameter("tel", dealer_did, -1)
        vCon.set_party_parameter("mailto", email, 0)
        vCon.set_party_parameter("name", full_name, 0)
        vCon.set_party_parameter("role", "agent", 0)
        vCon.set_party_parameter("extension", extension, 0)
        vCon.set_party_parameter("tel", customerNumber, -1)
        vCon.set_party_parameter("role", "customer", 1)
    else:
        vCon.set_party_parameter("tel", customerNumber, -1)
        vCon.set_party_parameter("role", "customer", 0)
        vCon.set_party_parameter("tel", dealer_did, -1)
        vCon.set_party_parameter("mailto", email, 1)
        vCon.set_party_parameter("name", full_name, 1)
        vCon.set_party_parameter("role", "agent", 1)
        vCon.set_party_parameter("extension", extension, 1)

    # We don't have the recording, but we have the rest of the dialog
    try:
        vCon.add_dialog_external_recording(b'', parse(start_time), duration, [0,1], external_url="")
    except Exception as e:
        logger.error("Error adding dialog recording: %s", e)


    # Set the adapter meta so we know where the this came from
    adapter_meta= {
        "adapter": "bria",
        "adapter_version": "0.1.0",
        "src": opts['ingress-list'],
        "type": 'call_completed',
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


async def start(opts=default_options):
    logger.info("Starting the bria adapter")
    # Setup redis
    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    while True:
        # logger.info("Bria adaptor loop")
        try:
            async with async_timeout.timeout(10):
                for ingress_list in opts["ingress-list"]:
                    data = await r.lpop(ingress_list)
                    if data is None:
                        continue
                    payload = json.loads(data)

                    records = payload.get("Records")
                    if records:
                        for record in records:
                            await handle_bria_s3_recording_event(record, opts, r)
                    else:
                        body = json.loads(payload.get("Message"))
                        await handle_bria_call_ended_event(body, opts, r)

        except asyncio.CancelledError:
            logger.info("Bria Cancelled")
            break
        except Exception:
            logger.error("bria adaptor error:\n%s", traceback.format_exc())

    logger.info("Bria adapter stopped")


def get_e164_number(phone_number: Optional[str]) -> str:
    if not phone_number:
        return ''
    parsed = phonenumbers.parse(phone_number, "US")
    the_return = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    logger.info("The return %s", the_return)
    return the_return