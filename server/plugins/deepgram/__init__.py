import redis.asyncio as redis
from redis.commands.json.path import Path
import asyncio
from lib.logging_utils import init_logger
import vcon
from settings import DEEPGRAM_KEY
from deepgram import Deepgram
import simplejson as json
import time

logger = init_logger(__name__)

r = redis.Redis(host='localhost', port=6379, db=0)

default_options = {
    "name": "deepgram",
    "ingress-topics": [],
    "egress-topics":[]
}
options = {}

async def run(vcon_uuid, opts=default_options, ):
    logger.info("deepgram plugin: processing vCon: {}".format(vcon_uuid))
    inbound_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())
    vCon = vcon.Vcon()
    vCon.loads(json.dumps(inbound_vcon))
    for index, dialog in enumerate(vCon.dialog):
        if dialog["type"] != "recording":
            logger.debug(f"deepgram plugin: skipping non-recording dialog {index} in vCon: {vcon_uuid}")
            continue

        if dialog["duration"] < 60:
            logger.debug(f"deepgram plugin: skipping short recording dialog {index} in vCon: {vcon_uuid}")
            continue

        logger.info("deepgram plugin: processing vCon: {}".format(vcon_uuid))
        logger.info("Duration of recording: {}".format(dialog["duration"]))

        
        # convert mp3 file to wav file
        filename = f"static/{str(vcon_uuid)}_{index}.wav"
        try:
            dg_client = Deepgram(DEEPGRAM_KEY)
            audio = open(filename, 'rb')
            source = {
            'buffer': audio,
            'mimetype': 'audio/x-wav'
            }
            transcription = await dg_client.transcription.prerecorded(source, 
                {   
                    'detect_topics': True,
                    'redact': 'pci',
                    'redact': 'ssn',
                    'diarize': True
                })
            result = transcription['results']['channels'][0]['alternatives'][0]
            transcript = result['transcript']
            words = result['words']
            topics = []
            for topic in result['topics']:
                topics += topic['topics']
            vCon.add_analysis_transcript(index, transcript, "deepgram", analysis_type="transcript")
            vCon.add_analysis_transcript(index, words, "deepgram", analysis_type="word_map")
            vCon.add_analysis_transcript(index, topics, "deepgram", analysis_type="topics")
        except Exception as e:
            logger.error("transcription plugin: error: {}".format(e))


    # Remove the NAN
    try:
        str_vcon = vCon.dumps()
        json_vcon = json.loads(str_vcon)
        str_vcon = json.dumps(json_vcon, ignore_nan=True)
        json_vcon = json.loads(str_vcon) 
        await r.json().set("vcon:{}".format(vCon.uuid), Path.root_path(), json_vcon)
        logger.info("deepgram plugin: processed vCon: {}".format(vcon_uuid))
        return vcon_uuid
    except Exception as e:
        logger.error("deepgram plugin: error: {}".format(e))
        return None

        
async def start(opts=default_options):
    logger.info("Starting the deepgram plugin")
    try:
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data'].decode('utf-8')
                    logger.info("deepgram plugin: received vCon: {}".format(vConUuid))
                    try:
                        # get the start time
                        st = time.time()
                        returnVconUuuid = await run(vConUuid, opts)
                        # get the end time
                        et = time.time()

                        # get the execution time
                        elapsed_time = et - st
                        logger.info(f'deepgram Execution time {elapsed_time} seconds')

                    except Exception as e:
                        logger.error("deepgram plugin threw unhandled error: {}".format(e))
                        returnVconUuuid = None

                    if returnVconUuuid:
                        for topic in opts['egress-topics']:
                            await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("deepgram plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("deepgram Cancelled")

    logger.info("deepgram stopped")    
