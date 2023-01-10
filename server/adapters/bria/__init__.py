import asyncio
import hashlib
import json
import logging
import logging.config
import traceback
from datetime import datetime
from typing import Optional
import copy

import async_timeout
import boto3
import phonenumbers
import redis.asyncio as redis
from dateutil.parser import parse
from redis.commands.json.path import Path
from settings import AWS_KEY_ID, AWS_SECRET_KEY, ENV, LOG_LEVEL, REDIS_URL

import vcon
from server.lib.vcon_redis import VconRedis

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.info("Bria adapter loading")

default_options = {
    "name": "bria",
    "ingress-list": [f"bria-conserver-feed-{ENV}"],
    "egress-topics": ["ingress-vcons"],
}


def time_diff_in_seconds(start_time: str, end_time: str) -> int:
    """Returns time difference in seconds for given start and end time

    Args:
        start_time (str): start time in iso string format (Z)
        end_time (str): end time in iso string format (Z)

    Returns:
        int: number of seconds between start and end time
    """
    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    duration = end_time - start_time
    return duration.seconds


def compute_redis_key(body):
    dealer_number = get_e164_number(body.get("dialerId"))
    customer_number = get_e164_number(body.get("customerNumber"))
    return f"bria:{dealer_number}:{customer_number}"


def add_bria_attachment(vCon, body, opts):
    # Set the adapter meta so we know where the this came from
    adapter_meta = {
        "adapter": "bria",
        "adapter_version": "0.1.0",
        "src": opts["ingress-list"],
        "type": "call_completed",
        "received_at": datetime.now().isoformat(),
        "payload": body,
    }
    vCon.attachments.append(adapter_meta)


def get_party_index(vcon, tel=None, extension=None):
    if tel:
        for ind, party in enumerate(vcon.parties):
            if party.get("tel") == tel:
                return ind
    if extension:
        for ind, party in enumerate(vcon.parties):
            if party.get("extension") == extension:
                return ind
    return -1


def add_dialog(vcon, body):
    start_time = body["startedAt"]
    end_time = body["endedAt"]
    duration = time_diff_in_seconds(start_time, end_time)

    email = body.get("email")
    username = email.split("@")[0]
    first_name = username.split(".")[0]
    last_name = username.split(".")[1]
    full_name = first_name + " " + last_name
    dealer_did = get_e164_number(body.get("dialerId"))
    customer_number = get_e164_number(body.get("customerNumber"))
    extension = body.get("extension")

    customer_index = get_party_index(vcon, tel=customer_number)
    if customer_index == -1:
        customer_index = vcon.add_party(
            {
                "tel": customer_number,
                "role": "customer",
            }
        )
    agent_index = get_party_index(vcon, extension=extension)
    if agent_index == -1:
        agent_index = vcon.add_party(
            {
                "tel": dealer_did,
                "mailto": email,
                "name": full_name,
                "role": "agent",
                "extension": extension,
            }
        )
    start_time = start_time.replace("Z", "+00:00")
    vcon.add_dialog_external_recording(
        body=None,
        start_time=start_time,
        duration=duration,
        parties=[customer_index, agent_index],
        mime_type="audio/x-wav",
        file_name=f"{body['id']}.wav",
        external_url=None,
    )


# async def handle_bria_call_started_event(body, r, vcon_redis):
#     logger.info("Processing call STARTED event %s", body)
#     key = compute_redis_key(body)
#     if (await r.exists(key)):
#         await r.persist(key) # reset the expire timeout so that key stays there till call ends
#     else:
#         vCon = vcon.Vcon() # TODO what additional data we need to add here
#         await vcon_redis.store_vcon(vCon)
#         await r.set(key, vCon.uuid) # NOTE what if we never receive call ended? The key will be infinite.
#         await r.expire(key, 3600)


async def handle_bria_call_ended_event(body, opts, r, vcon_redis):
    logger.info("Processing call ENDED event %s", body)
    # Construct empty vCon, set meta data
    redis_key = compute_redis_key(body)
    vcon_id = await r.get(redis_key)
    vCon = None
    if not vcon_id:
        vCon = vcon.Vcon()
        await r.set(redis_key, vCon.uuid)
    else:
        vCon = await vcon_redis.get_vcon(vcon_id)
    logger.info(f"The vcon id is {vCon.uuid}")
    await r.expire(redis_key, 3600)
    add_dialog(vCon, body)
    add_bria_attachment(vCon, body, opts)
    await vcon_redis.store_vcon(vCon)
    for egress_topic in opts["egress-topics"]:
        await r.publish(egress_topic, vCon.uuid)


def create_presigned_url(
    bucket_name: str, object_key: str, expiration: int = 3600
) -> str:
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_key: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client(
        "s3", aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
    except Exception as e:
        logging.error(e)  # TODO should we rethrow this error???
        return None

    # The response contains the presigned URL
    return response


def create_sha512_hash_for_s3_file(bucket_name: str, object_key: str) -> str:
    s3 = boto3.client(
        "s3", aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY
    )
    # Retrieve the file from S3 and calculate the SHA-512 fingerprint
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    contents = response["Body"].read()
    fingerprint = hashlib.sha512(contents).hexdigest()
    return fingerprint


HUNDREAD_YEARS_SECONDS = 3.156e8


async def handle_bria_s3_recording_event(record, opts, redis_client, vcon_redis):
    """Called when new s3 event is received. This function will update dialog object in vcon with correct url for recording and hash checksum

    Args:
        record (s3 event): s3 event object
        opts (dict): _description_
        r (redis_client): Redis client
        vcon_redis (VconRedis): Instance of vcon redis
    """
    logger.info("Processing s3 recording %s", record)
    s3_object_key = record["s3"]["object"]["key"]
    s3_bucket_name = record["s3"]["bucket"]["name"]
    bria_call_id = s3_object_key.replace(".wav", "")
    # lookup the vCon in redis using this ID
    # FT.SEARCH idx:adapterIdIndex '@adapter:{bria} @id:{f8be045704cb4ea98d73f60a88590754}'
    result = await redis_client.ft(index_name="idx:adapterIdsIndex").search(
        f"@adapter:{{bria}} @id:{{{bria_call_id}}}"
    )
    v_con = vcon.Vcon()
    v_con.loads(result.docs[0].json)
    for index, dialog in enumerate(v_con.dialog):
        if dialog.get("filename") == f"{bria_call_id}.wav":
            # TODO https:// find a way to get https link with permenent access
            v_con.dialog[index]["url"] = create_presigned_url(
                s3_bucket_name, s3_object_key, HUNDREAD_YEARS_SECONDS
            )
            v_con.dialog[index]["signature"] = create_sha512_hash_for_s3_file(
                s3_bucket_name, s3_object_key
            )
            v_con.dialog[index]["alg"] = "SHA-512"
    await vcon_redis.store_vcon(v_con)
    for egress_topic in opts["egress-topics"]:
        await redis_client.publish(egress_topic, v_con.uuid)


async def start(opts=None):
    """Starts the bria adaptor as co-routine. This adaptor will run till it's killed.

    Args:
        opts (Defalut options, optional): Options which controls behaviour of this adaptor. Defaults to None.
    """
    if opts is None:
        opts = copy.deepcopy(default_options)
    logger.info("Starting the bria adapter")
    # Setup redis
    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    vcon_redis = VconRedis(redis_client=r)
    while True:
        # logger.info("Bria adaptor loop")
        try:
            # Terminate if it takes longer than 10 sec
            async with async_timeout.timeout(10):
                for ingress_list in opts["ingress-list"]:
                    data = await r.lpop(ingress_list)
                    if data is None:
                        # If ingress_list is not exists in the Redis it will return None
                        continue
                    payload = json.loads(data)
                    records = payload.get("Records")
                    if records:
                        for record in records:
                            await handle_bria_s3_recording_event(
                                record, opts, r, vcon_redis
                            )
                    else:
                        body = json.loads(payload.get("Message"))
                        event_type = payload["MessageAttributes"]["kind"]["Value"]
                        if event_type == "call_ended":
                            await handle_bria_call_ended_event(
                                body, opts, r, vcon_redis
                            )
                        # elif event_type == "call_started":
                        #     await handle_bria_call_started_event(body, r, vcon_redis)
                        else:
                            logger.info(f"Ignoring the Event Type : {event_type}")
        except asyncio.CancelledError:
            logger.info("Bria Cancelled")
            break
        except Exception:
            logger.error("bria adaptor error:\n%s", traceback.format_exc())

    logger.info("Bria adapter stopped")


def get_e164_number(phone_number: Optional[str]) -> str:
    """Returns the phone number in E164 format

    Args:
        phone_number (Optional[str]): the phone number to be formated to E164

    Returns:
        str: phone number formated in E164 format
    """
    if not phone_number:
        return ""
    parsed = phonenumbers.parse(phone_number, "US")
    the_return = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    logger.info("The return %s", the_return)
    return the_return
