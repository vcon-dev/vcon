import asyncio
import redis.asyncio as redis
import json
import vcon
import logging
import datetime
import whisper
from settings import LOG_LEVEL, REDIS_URL
import traceback
from redis.commands.json.path import Path


r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

model = whisper.load_model("base")

default_options = {
    "name": "call_log",
    "ingress-topics": ["ingress-vcons"],
    "transcribe": True,
    "min_transcription_length": 10,
    "deepgram": False,
    "egress-topics":[],
}

async def run(vcon_uuid, opts=default_options):
    inbound_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        vCon.loads(json.dumps(inbound_vcon))

        projection = {}
        # Extract the parties from the vCon
        projection['projection'] = 'call_log'
        for party in vCon.parties:
            if party['role'] == 'customer':
                projection['customer_number'] = party['tel']
            if party['role'] == 'agent':
                projection['extension'] = party['extension']
                projection['dealer_number'] = party['tel']
        
        if vCon.parties[0]['role'] == 'customer':
            projection['direction'] = 'inbound'
        else:
            projection['direction'] = 'outbound'

        for dialog in vCon.dialog:
            if dialog['type'] == 'recording':
                projection['call_started_on'] = dialog['start']
                projection['duration'] = dialog['duration']

        projection['created_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        projection['modified_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        dealer_name = vCon.attachments[0]["payload"].get("dealerName")
        if dealer_name:
            projection["dealer_cached_details"] = {"name": dealer_name}
        vCon.attachments.append(projection)

        # Send this out to the storage adapters
        str_vcon = vCon.dumps()
        json_vcon = json.loads(str_vcon)
        await r.json().set("vcon:{}".format(vCon.uuid), Path.root_path(), json_vcon)

        return(vCon)
    except:
        logger.error("call_log plugin: error: \n%s", traceback.format_exc())
        logger.error("Shoot!")

async def start(opts=default_options):
    logger.info("Starting the call_log plugin")
    try:
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data']
                    logger.info(f"call_log plugin: received vCon: {vConUuid}")
                    await run(vConUuid, opts)
                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("call_log plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("call_log Cancelled")

    logger.info("call_log stopped")    