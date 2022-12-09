import asyncio
import redis.asyncio as redis
import asyncio
import logging
import vcon
from redis.commands.json.path import Path
import json
import os
import simplejson as json

from stable_whisper import load_model
from stable_whisper import stabilize_timestamps

from settings import LOG_LEVEL

r = redis.Redis(host='localhost', port=6379, db=0)

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

default_options = {
    "name": "transcription",
    "ingress-topics": ["ingress-vcons"],
    "egress-topics":[],
}
model = load_model("base")

options = {}

async def run(vcon_uuid, opts=default_options, ):
    inbound_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())

    # Make sure that this vCon actually has a dialog to transcribe
    # If not, just return
    for i, dialog in enumerate(inbound_vcon['dialog']):
        if dialog["type"] != 'recording':
            continue

        # Look, there's a dialog
        # Let's transcribe it. 
        # Gotta find that audio file
        vCon = vcon.Vcon()
        vCon.loads(json.dumps(inbound_vcon))
        bytes = vCon.decode_dialog_inline_recording(i)
        # Load the audio from the vCon, use a temporary
        # file to avoid loading the entire audio into memory
        tmp_file = open("_temp_file", 'wb')
        tmp_file.write(bytes)
        tmp_file.close()
        results = model.transcribe("_temp_file", ts_num=7, stab=False, fp16=False, verbose=True)
        # Remove temp file
        os.remove("_temp_file")

        vCon.add_analysis_transcript(i, results, "whisper-ai")
        str_vcon = vCon.dumps()
        json_vcon = json.loads(str_vcon)
        # Remove the NAN
        str_vcon = json.dumps(json_vcon, ignore_nan=True)
        json_vcon = json.loads(str_vcon) 
        try:
            await r.json().set("vcon:{}".format(vCon.uuid), Path.root_path(), json_vcon)
        except Exception as e:
            logger.error("transcription plugin: error: {}".format(e))

    

async def start(opts=default_options):
    logger.info("Starting the transcription plugin")
    try:
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data'].decode('utf-8')
                    logger.info("transcription plugin: received vCon: {}".format(vConUuid))
                    run(opts, vConUuid)
                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("transcription plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("transcription Cancelled")

    logger.info("transcription stopped")    



