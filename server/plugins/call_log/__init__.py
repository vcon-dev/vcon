import asyncio
import redis.asyncio as redis
import json
import vcon
import asyncio
import logging
import datetime
import whisper


logger = logging.getLogger(__name__)
model = whisper.load_model("base")

default_options = {
    "name": "call_log",
    "ingress-topics": ["ingress-vcons"],
    "transcribe": True,
    "min_transcription_length": 10,
    "deepgram": False,
    "egress-topics":["egress-vcons-1"],
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

            vCon.attachments.append(projection)

        # Send this out to the storage adapters
        return(vCon)
    
    except Exception as e:
        logger.error("call_log plugin: error: {}".format(e))
        logger.error("Shoot!")
        logger.info("call_log error: {}".format(e))

async def start(opts=default_options):
    logger.info("Starting the call_log plugin")

    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            message = await p.get_message()
            if message:
                
                vConUuid = message['data'].decode('utf-8')
                logger.info("call_log plugin: received vCon: {}".format(vConUuid))
                vCon = await r.json().get("vcon:"+vConUuid)
                vCon = await manage_ended_call(vCon)
                if not vCon:
                    continue
                for topic in opts['egress-topics']:
                    await r.publish(topic, vCon.uuid)
            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        logger.debug("call log plugin Cancelled")


    logger.info("call log plugin stopped")    



