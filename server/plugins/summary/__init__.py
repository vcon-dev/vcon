import redis.asyncio as redis
from redis.commands.json.path import Path
import asyncio
import logging
import vcon
import jose
import os
from pydub import AudioSegment
from settings import DEEPGRAM_KEY
from deepgram import Deepgram
from settings import LOG_LEVEL
import simplejson as json

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
r = redis.Redis(host='localhost', port=6379, db=0)

default_options = {
    "name": "summary",
    "ingress-topics": ["test-summary"],
    "egress-topics":[]
}
options = {}

async def run(vcon_uuid, opts=default_options, ):
    inbound_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())
    vCon = vcon.Vcon()
    vCon.loads(json.dumps(inbound_vcon))
    for index, dialog in enumerate(vCon.dialog):
        if dialog["type"] != "recording":
            continue
        
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
                    'summarize': True,
                    'detect_topics': True,
                    'redact': 'pci',
                    'redact': 'ssn'

                })
            result = transcription['results']['channels'][0]['alternatives'][0]
            full_summary = ""
            for summary in result['summaries']:
                full_summary += summary['summary'] + ". "
            transcript = result['transcript']
            words = result['words']
            topics = []
            for topic in result['topics']:
                topics += topic['topics']
            vCon.add_analysis_transcript(index, transcript, "deepgram", analysis_type="transcript")
            vCon.add_analysis_transcript(index, full_summary, "deepgram", analysis_type="summary")
            vCon.add_analysis_transcript(index, words, "deepgram", analysis_type="word_map")
            vCon.add_analysis_transcript(index, topics, "deepgram", analysis_type="topics")


            # Remove the NAN
            str_vcon = vCon.dumps()
            json_vcon = json.loads(str_vcon)
            str_vcon = json.dumps(json_vcon, ignore_nan=True)
            json_vcon = json.loads(str_vcon) 
            await r.json().set("vcon:{}".format(vCon.uuid), Path.root_path(), json_vcon)
        except Exception as e:
            logger.error("transcription plugin: error: {}".format(e))

        
async def start(opts=default_options):
    logger.info("Starting the summary plugin")
    try:
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data'].decode('utf-8')
                    logger.info("summary plugin: received vCon: {}".format(vConUuid))
                    run(opts, vConUuid)
                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("summary plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("summary Cancelled")

    logger.info("summary stopped")    
