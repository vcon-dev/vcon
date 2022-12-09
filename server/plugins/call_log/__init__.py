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

async def manage_ended_call(inbound_vcon):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        vCon.loads(json.dumps(inbound_vcon))

        if not vCon.dialog: 
            logger.debug("call_log plugin: vCon has no dialog, skipping")
            return
        
        # Check to see if this is a voice call
        voice = False
        for dialog in vCon.dialog:
            if dialog.get("type") == "recording":
                voice = True
                break

        if not voice:
            logger.debug("call_log plugin: vCon is not a voice call, skipping")
            return

        for dialog in vCon.dialog:
            projection = {}
            if vCon.attachments[0]["payload"]["direction"]=="out":
                projection['customer_number'] = vCon.parties[1]['tel']
                projection['extension'] = vCon.parties[0]['tel']
            else:
                projection['customer_number'] = vCon.parties[0]['tel']
                projection['extension'] = vCon.parties[1]['tel']
            projection['dealer_number'] = vCon.attachments[0]['payload']['dialerId']
            projection['call_started_on'] = dialog['start']
            projection['duration'] = dialog['duration']
            projection['created_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            projection['modified_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            projection['projection'] = 'call_log'

            """
            attachments: [
                {adapter: bria, type: call_recording, ...},
                {projection: call_log, ...},
                {lead: "cars.com", adf: <adf-data>},
            ]
            """

            # Check to see if there's more information in the vCon
            for party in vCon.parties:
                if 'direction' in party:
                    projection['direction'] = party['direction']
                if 'disposition' in party:
                    projection['disposition'] = party['disposition']

            vCon.attachments.append(projection)

        # Send this out to the storage adapters
        return(vCon)
    except:
        logger.error("call_log plugin: error: \n%s", traceback.format_exc())
        logger.error("Shoot!")


async def start(opts=default_options):
    logger.info("Starting the call_log plugin!!!")
    while True:
        try:
            r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
            p = r.pubsub(ignore_subscribe_messages=True)
            await p.subscribe(*opts['ingress-topics'])
            async for message in p.listen():
                vConUuid = message['data']
                logger.info("call_log plugin: received vCon: {}".format(vConUuid))
                vCon = await r.json().get("vcon:"+vConUuid)
                vCon = await manage_ended_call(vCon)
                if not vCon:
                    continue
                key = f"vcon:{vCon.uuid}"
                cleanvCon = json.loads(vCon.dumps())
                await r.json().set(key, Path.root_path(), cleanvCon)
                for topic in opts['egress-topics']:
                    await r.publish(topic, vCon.uuid)
        except asyncio.CancelledError:
            logger.debug("call log plugin Cancelled")
            break
        except Exception:
            logger.error("call_log plugin: error: \n%s", traceback.format_exc())
            logger.error("Shoot!")
    logger.info("call log plugin stopped")



