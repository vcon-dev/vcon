import asyncio
import async_timeout
import redis.asyncio as redis
import json
import vcon
import asyncio
import pymongo
from settings import MONGODB_URL, DEEPGRAM_KEY
import logging
import datetime
import whisper
import jose
import numpy
from pydub import AudioSegment
import uuid
import os
import torch
import time
from deepgram import Deepgram


logger = logging.getLogger(__name__)
model = whisper.load_model("base")

options = {
    "name": "call_log",
    "transcribe": True,
    "min_transcription_length": 10,
    "deepgram": True,
}

async def transcribe_deepgram(dialog):
    try:
        mimetype = dialog['mimetype']
        match mimetype:
            case "audio/ogg":
                filename = "/tmp/{}.ogg".format(uuid.uuid4())
            case "audio/x-wav":
                filename = "/tmp/{}.wav".format(uuid.uuid4())

        decoded_body = jose.utils.base64url_decode(bytes(dialog["body"], 'utf-8'))
        f = open(filename, "wb")
        f.write(decoded_body)
        f.close()

        # Transcribe the call 
        st = time.time()
        logger.info("Transcribing call with DeepGram: duration: {} seconds".format(dialog['duration']))

        # Transcribe it
        dg_client = Deepgram(DEEPGRAM_KEY)
        audio = open(filename, 'rb')
        source = {
        'buffer': audio,
        'mimetype': mimetype,
        }
        transcription = await dg_client.transcription.prerecorded(source, 
            {   'punctuate': True,
                'diarize': True,
                'multichannel': False,
                'language': 'en',
                'model': 'general',
                'punctuate': True,
                'tier':'enhanced',
            })
        # get the end time
        et = time.time()

        # get the execution time
        elapsed_time = et - st
        logger.info("Transcription Execution time: {} seconds".format(elapsed_time))
        logger.info("Transcription: {}".format(transcription))

        os.remove(filename)
        return transcription['results']
    except BaseException as e:
        logger.info("DeepGram error: {}".format(e))



async def transcribe(dialog):
    filename = "/tmp/{}.ogg".format(uuid.uuid4())
    decoded_body = jose.utils.base64url_decode(bytes(dialog["body"], 'utf-8'))
    f = open(filename, "wb")
    f.write(decoded_body)
    f.close()

    # Transcribe the call 
    st = time.time()
    logger.info("Transcribing call with Whisper: duration: {} seconds".format(dialog['duration']))
    decoded_body = jose.utils.base64url_decode(bytes(dialog["body"], 'utf-8'))
    result = model.transcribe(filename, fp16=False)
    # get the end time
    et = time.time()

    # get the execution time
    elapsed_time = et - st
    logger.info("Transcription Execution time: {} seconds".format(elapsed_time))
    logger.info("Transcription: {}".format(result))

    os.remove(filename)
    return result

async def manage_ended_call(inbound_vcon, redis_client, mongo_client):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        vCon.loads(json.dumps(inbound_vcon))

        if not vCon.dialog: 
            logger.debug("call_log plugin: vCon has no dialog, skipping")
            return
        
        # Check to see if this is a voice call
        voice = True
        for party in vCon.parties:
            if 'mailto' in party:
                voice = False

        if not voice:
            logger.debug("call_log plugin: vCon is not a voice call, skipping")
            return

        for dialog in vCon.dialog:
            projection = {}
            projection['customer_number'] = vCon.parties[0]['tel']
            projection['dealer_number'] = vCon.parties[1]['tel']
            projection['call_started_on'] = dialog['start']
            projection['duration'] = dialog['duration']
            projection['created_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            projection['modified_on']= datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")


            # Check to see if there's more information in the vCon
            for party in vCon.parties:
                if 'direction' in party:
                    projection['direction'] = party['direction']
                if 'disposition' in party:
                    projection['disposition'] = party['disposition']

            # Transcribe the recording
            if options['transcribe'] and dialog['duration'] > options['min_transcription_length']:
                if options['deepgram']:
                    result = await transcribe_deepgram(dialog)
                    transcription = result['channels'][0]['alternatives'][0]['transcript']

                else:
                    result = await transcribe(dialog)
                    transcription = result['text']
                projection['transcription'] = transcription

            vCon.attachments.append(projection)

        # Send this out to the storage adapters
        await redis_client.publish("storage-events", vCon.dumps())
    
    except Exception as e:
        logger.info("call_log error: {}".format(e))

async def start():
    logger.info("Starting the call_log plugin")

    while True:
        try:
            async with async_timeout.timeout(500):
                # Setup redis
                r = redis.Redis(host='localhost', port=6379, db=0)
                m = pymongo.MongoClient(MONGODB_URL)
                pubsub = r.pubsub()
                await pubsub.subscribe("ingress-vcons")
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        body = json.loads(message['data'].decode())
                        logger.info("call_log received vCon: {}".format(body['uuid']))
                        await manage_ended_call(body, r, m)
                        await asyncio.sleep(1)

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            logger.debug("call log plugin Cancelled")
            break

    logger.info("call log plugin stopped")    



