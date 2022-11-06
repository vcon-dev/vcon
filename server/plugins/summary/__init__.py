import redis.asyncio as redis
import asyncio
import logging
import vcon
import jose
from pydub import AudioSegment
from settings import DEEPGRAM_KEY
from deepgram import Deepgram


logger = logging.getLogger(__name__)
default_options = {
    "name": "redaction",
    "ingress-topics": ["test-summary"],
    "egress-topics":[],
    "redaction-topics":["ADDRESS", "DRIVERS_LICENSE", "PERSON", "PHONE_NUMBER",
    "DATE", "INTEGER"],
    "redaction-character": "@"
}
options = {}

# Utility functions
def has_voice(vCon):
    for party in vCon.parties:
        if "tel" in party:
            return True
    return False

async def start(opts=default_options):
    logger.info("Starting the redaction plugin")

    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data'].decode('utf-8')
                    body = await r.get("vcon-{}".format(str(vConUuid)))
                    vCon = vcon.Vcon()
                    vCon.loads(body)

                    if has_voice(vCon):
                        index = 0
                        for dialog in vCon.dialog: 
                            wav_filename = "static/{}_{}.wav".format(id, index)
                            decoded_body = jose.utils.base64url_decode(bytes(dialog["body"], 'utf-8'))
                            f = open(wav_filename, "wb")
                            f.write(decoded_body)
                            f.close()
                            # convert mp3 file to wav file
                            sound = AudioSegment.from_file(wav_filename)
                            sound.export(wav_filename, format="wav")
                            dg_client = Deepgram(DEEPGRAM_KEY)
                            audio = open(wav_filename, 'rb')
                            source = {
                            'buffer': audio,
                            'mimetype': 'audio/x-wav'
                            }
                            transcription = await dg_client.transcription.prerecorded(source, 
                                {   
                                    'summarize': True,
                                })
                            index+=1

                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("summary plugin: error: {}".format(e))


    except asyncio.CancelledError:
        logger.debug("summary Cancelled")

    logger.info("summary stopped")    



