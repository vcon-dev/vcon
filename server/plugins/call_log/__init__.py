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
from server.lib.vcon_redis import VconRedis
import copy

r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
vcon_redis = VconRedis(redis_client=r)

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

async def run(vcon_uuid):
    try:
        # Construct empty vCon, set meta data
        vCon = await vcon_redis.get_vcon(vcon_uuid)
        projection_index = -1
        for index,attachment in enumerate(vCon.attachments):
            if attachment.get("projection") == "call_log":
                projection_index = index
                break
            
        projection = get_projection(vCon)
        if projection_index>-1:
            vCon.attachments[projection_index] = projection
        else:
            vCon.attachments.append(projection)
        await vcon_redis.store_vcon(vCon)
        return(vCon)

    except Exception:
        logger.error("call_log plugin: error: \n%s", traceback.format_exc())
        logger.error("Shoot!")


def get_projection(vCon):
    projection = {}
    # Extract the parties from the vCon
    projection['projection'] = 'call_log'
    for party in vCon.parties:
        if party['role'] == 'customer':
            projection['customer_number'] = party['tel']
        if party['role'] == 'agent':
            projection['extension'] = party['extension']
            projection['dealer_number'] = party['tel']
    
    
    projection['direction'] = vCon.attachments[0]["payload"]["direction"].upper()

    projection['created_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    projection['modified_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    projection['call_started_on'] = vCon.attachments[0]["payload"]["startedAt"]
    projection['id'] = vCon.uuid
    projection['dialog'] = copy.deepcopy(vCon.dialog)
    add_agent_extension_to_dialog(vCon, projection['dialog'])
    projection['disposition'] = get_overall_disposition(vCon.dialog)
    projection['duration'] = calculate_duration(vCon.dialog)
    dealer_name = vCon.attachments[0]["payload"].get("dealerName")
    if dealer_name:
        projection["dealer_cached_details"] = {"name": dealer_name}
    # vCon.attachments.append(projection)
    return projection

def calculate_duration(dialog):
    duration = 0
    for dialog_item in dialog:
        duration += dialog_item["duration"]
    return duration

def get_overall_disposition(dialog):
    for dialog_item in dialog:
        if dialog_item["disposition"] == 'ANSWERED':
            return 'ANSWERED'

    return 'MISSED'

def add_agent_extension_to_dialog(vCon, dialog):
    for dialog_item in dialog:
        # get the agent's extension
        agent_idx = dialog_item["parties"][-1]
        dialog_item["agent_extension"] = vCon.parties[agent_idx]["extension"]
        dialog_item["agent_name"] = vCon.parties[agent_idx]["name"]


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
                    await run(vConUuid)
                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("call_log plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("call_log Cancelled")

    logger.info("call_log stopped")    