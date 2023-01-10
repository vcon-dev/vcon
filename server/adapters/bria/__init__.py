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
import boto3
import hashlib
from settings import AWS_KEY_ID, AWS_SECRET_KEY

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.info('Bria adapter loading')

default_options = {
    "name": "bria",
    "ingress-list": [f"bria-conserver-feed-{ENV}"],
    "egress-topics":["ingress-vcons"],
}


def time_diff_in_seconds(start_time: str, end_time: str) -> int:
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
    adapter_meta= {
        "adapter": "bria",
        "adapter_version": "0.1.0",
        "src": opts['ingress-list'],
        "type": 'call_completed',
        "received_at": datetime.now().isoformat(),
        "payload": body
    }
    vCon.attachments.append(adapter_meta)


async def store_vcon(vCon, r):
    key = f"vcon:{vCon.uuid}"
    cleanvCon = json.loads(vCon.dumps())
    await r.json().set(key, Path.root_path(), cleanvCon)


async def get_vcon(vcon_id, r):
    vcon_dict = await r.json().get(f"vcon:{vcon_id}", Path.root_path())
    _vcon = vcon.Vcon()
    _vcon.loads(json.dumps(vcon_dict))
    return _vcon


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
    start_time = body['startedAt']
    end_time = body['endedAt']
    duration = time_diff_in_seconds(start_time, end_time)

    email = body.get("email")
    username = email.split('@')[0]
    first_name = username.split('.')[0]
    last_name = username.split('.')[1]
    full_name = first_name + " " + last_name
    dealer_did = get_e164_number(body.get("dialerId"))
    customer_number = get_e164_number(body.get("customerNumber"))
    extension = body.get("extension")

    customer_index = get_party_index(vcon, tel=customer_number)
    if customer_index == -1:
        customer_index = vcon.add_party({
            "tel": customer_number,
            "role": "customer",
        })
    agent_index = get_party_index(vcon, extension = extension)
    if agent_index == -1:
        agent_index = vcon.add_party({
            "tel": dealer_did,
            "mailto": email,
            "name":  full_name,
            "role": "agent",
            "extension": extension,
        })
    start_time = start_time.replace('Z', '+00:00')
    vcon.add_dialog_external_recording(
        body=None,
        start_time=start_time,
        duration = duration,
        parties = [customer_index, agent_index],
        mime_type = "audio/x-wav",
        file_name = f"{body['id']}.wav",
        external_url = None
    )



# async def handle_bria_call_started_event(body, r):
#     logger.info("Processing call STARTED event %s", body)
#     key = compute_redis_key(body)
#     if (await r.exists(key)):
#         await r.persist(key) # reset the expire timeout so that key stays there till call ends
#     else:
#         vCon = vcon.Vcon() # TODO what additional data we need to add here
#         await store_vcon(vCon, r)
#         await r.set(key, vCon.uuid) # NOTE what if we never receive call ended? The key will be infinite.
#         await r.expire(key, 3600)


async def handle_bria_call_ended_event(body, opts, r):
    logger.info("Processing call ENDED event %s", body)
    # Construct empty vCon, set meta data
    redis_key = compute_redis_key(body)
    vcon_id = await r.get(redis_key)
    vCon = None
    if not vcon_id:
        vCon = vcon.Vcon()
        await r.set(redis_key, vCon.uuid)
    else:
        vCon = await get_vcon(vcon_id, r)
    logger.info(f"The vcon id is {vCon.uuid}")
    await r.expire(redis_key, 3600)
    add_dialog(vCon, body)
    add_bria_attachment(vCon, body, opts)
    await store_vcon(vCon, r)
    for egress_topic in opts["egress-topics"]:
        await r.publish(egress_topic, vCon.uuid)


def create_presigned_url(bucket_name: str, object_key: str, expiration: int = 3600) -> str:
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_key: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3', aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY)
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_key},
                                                    ExpiresIn=expiration)
    except Exception as e:
        logging.error(e) # TODO should we rethrow this error???
        return None

    # The response contains the presigned URL
    return response


def create_sha512_hash_for_s3_file(bucket_name: str, object_key: str) -> str:
    s3 = boto3.client('s3', aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY)
    # Retrieve the file from S3 and calculate the SHA-512 fingerprint
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    contents = response['Body'].read()
    fingerprint = hashlib.sha512(contents).hexdigest()
    return fingerprint


HUNDREAD_YEARS_SECONDS = 3.156e+8
async def handle_bria_s3_recording_event(record, opts, r):
    logger.info("Processing s3 recording %s", record)
    s3_object_key = record["s3"]["object"]["key"]
    s3_bucket_name = record["s3"]["bucket"]["name"]
    bria_call_id = s3_object_key.replace('.wav', '')
    # lookup the vCon in redis using this ID
    # FT.SEARCH idx:adapterIdIndex '@adapter:{bria} @id:{f8be045704cb4ea98d73f60a88590754}'
    result = await r.ft(index_name="idx:adapterIdsIndex").search(f"@adapter:{{bria}} @id:{{{bria_call_id}}}")
    vCon = vcon.Vcon()
    vCon.loads(result.docs[0].json)
    for index, d in enumerate(vCon.dialog):
        if d.get("filename") == f"{bria_call_id}.wav":
            # TODO https:// find a way to get https link with permenent access
            vCon.dialog[index]["url"] = create_presigned_url(s3_bucket_name, s3_object_key, HUNDREAD_YEARS_SECONDS)
            vCon.dialog[index]['signature'] = create_sha512_hash_for_s3_file(s3_bucket_name, s3_object_key)
            vCon.dialog[index]['alg'] = "SHA-512"
    await store_vcon(vCon, r)
    for egress_topic in opts["egress-topics"]:
        await r.publish(egress_topic, vCon.uuid)


async def start(opts=default_options):
    logger.info("Starting the bria adapter")
    # Setup redis
    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
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
                            await handle_bria_s3_recording_event(record, opts, r)
                    else:
                        body = json.loads(payload.get("Message"))
                        event_type = payload["MessageAttributes"]["kind"]["Value"]
                        if event_type == "call_ended":
                            await handle_bria_call_ended_event(body, opts, r)
                        # elif event_type == "call_started":
                        #     await handle_bria_call_started_event(body, r)
                        else:
                            logger.info(f"Ignoring the Event Type : {event_type}")
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