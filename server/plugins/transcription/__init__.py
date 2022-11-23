import asyncio
import redis.asyncio as redis
import asyncio
import logging
import whisper
import vcon
from redis.commands.json.path import Path

import plugins.transcription.stable_whisper
from settings import LOG_LEVEL


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

default_options = {
    "name": "transcription",
    "ingress-topics": ["ingress-vcons"],
    "egress-topics":[],
}
options = {}

async def start(opts=default_options):
    logger.info("Starting the transcription plugin")

    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data'].decode('utf-8')
                    logger.info("transcription plugin: received vCon: {}".format(vConUuid))
                    body = await r.get("vcon:{}".format(str(vConUuid)))
                    vCon = vcon.Vcon()
                    vCon.loads(body)

                    # Make sure that this vCon actually has a dialog to transcribe
                    voice = False
                    for dialog in vCon.dialog:
                        if dialog["type"] == 'recording':
                            voice = True
                    
                    if not voice:
                        # No voice, go home.
                        for topic in opts['egress-topics']:
                            await r.publish(topic, vConUuid)
                        return

                    model = whisper.load_model("base")
                    stable_whisper.modify_model(model)
                    # Load the audio from the vCon, use a temporary
                    # file to avoid loading the entire audio into memory
                    bytes = vCon.decode_dialog_inline_recording(0)
                    tmp_file = open("_temp_file", 'wb')
                    tmp_file.write(bytes)
                    tmp_file.close()

                    # load audio and pad/trim it to fit 30 seconds
                    # ts_num=7 is num of timestamps to get, so 7 is more than the default of 5
                    # stab=True  is disable stabilization so you can do it later with different settings
                    transcript = model.transcribe("_temp_file", ts_num=7, stab=False, fp16=False, verbose=True)
                    stabilized_segments = stable_whisper.stabilize_timestamps(transcript["segments"], aggressive=True)
                    transcript['segments'] = stabilized_segments
                    vCon.add_analysis_transcript(0, transcript, "whisper-ai")
                    await r.json().set("vcon:{}".format(vCon.uuid), Path.root_path(), vCon.dumps())
                    
                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("transcription plugin: error: {}".format(e))


    except asyncio.CancelledError:
        logger.debug("transcription Cancelled")

    logger.info("transcription stopped")    



