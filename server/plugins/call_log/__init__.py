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
            break

    main_agent, projection['disposition'] = get_main_agent_and_disposition(vCon)
    projection['extension'] = main_agent['extension']
    projection['agent_name'] = main_agent['name']
    projection['dealer_number'] = main_agent['tel']

    projection['direction'] = vCon.attachments[0]["payload"]["direction"].upper()

    projection['created_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    projection['modified_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    projection['call_started_on'] = vCon.attachments[0]["payload"]["startedAt"]
    projection['id'] = vCon.uuid
    projection['dialog'] = compute_dialog_projection(vCon.dialog)
    add_agent_extension_to_dialog(vCon, projection['dialog'])

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

def get_agent_from_dialog_item(dialog_item,vCon):
    for party_idx in dialog_item["parties"]:
        party = vCon.parties[party_idx]
        if party["role"]=="agent":
            return party
    return None

# main agent/extenst is whoever last answered the call or the last agent if no one answered
def get_main_agent_and_disposition(vCon):
    main_dialog_item = None
    copy_dialog = compute_dialog_projection(vCon.dialog)
    dialog_reversed = list(reversed(copy_dialog))
    answered_dispositions = ["ANSWERED", "INTERNAL TRANSFER"]
    for dialog_item in dialog_reversed:
        if dialog_item["disposition"] in answered_dispositions:
            main_dialog_item = dialog_item
            break
    if not main_dialog_item:
        main_dialog_item = dialog_reversed[0]

    agent = get_agent_from_dialog_item(main_dialog_item,vCon)
    main_disposition = main_dialog_item["disposition"]
    if main_disposition in answered_dispositions:
        main_disposition = "ANSWERED"
    return agent, main_disposition


def add_agent_extension_to_dialog(vCon, dialog):
    for dialog_item in dialog:
        # get the agent's extension
        agent_idx = dialog_item["parties"][-1]
        dialog_item["agent_extension"] = vCon.parties[agent_idx]["extension"]
        dialog_item["agent_name"] = vCon.parties[agent_idx]["name"]

def compute_dialog_projection(dialog):
    copied_dialog = copy.deepcopy(dialog)
    copied_dialog.sort(key=lambda x: x['start'])
    for ind, dialog_item in enumerate(copied_dialog):
        if dialog_item["disposition"] == "ANSWERED":
            if ind < len(copied_dialog)-1:
                dialog_item["disposition"] = "INTERNAL TRANSFER"
        if dialog_item["disposition"] == "MISSED":
            if dialog_item["duration"] < 4:
                if ind == len(copied_dialog) - 1:
                    dialog_item["disposition"] = "HUNG UP"
                else:
                    dialog_item["disposition"] = "DECLINED"
            elif dialog_item["duration"] < 12:
                if ind < len(copied_dialog) - 1:
                    dialog_item["disposition"] = "DECLINED"
    return copied_dialog


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