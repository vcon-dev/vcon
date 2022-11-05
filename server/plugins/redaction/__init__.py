import asyncio
import redis.asyncio as redis
import asyncio
import logging
import vcon
from dataprofiler import Data, Profiler
from dataprofiler.data_readers.text_data import TextData
import dataprofiler as dp

import json

logger = logging.getLogger(__name__)
default_options = {
    "name": "redaction",
    "ingress-topics": ["ingress-vcons"],
    "egress-topics":[],
    "redaction-topics":["ADDRESS", "DRIVERS_LICENSE", "PERSON", "PHONE_NUMBER",
    "DATE", "INTEGER"],
    "redaction-character": "@"
}
options = {}

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

                    for analysis in vCon.analysis:
                        if analysis['vendor'] != 'whisper-ai':
                            continue
                        text = analysis['body']['text']
                        data = TextData(data=text) # Auto-Detect & Load: CSV, AVRO, Parquet, JSON, Text, URL
                        profile = Profiler(data) # Calculate Statistics, Entity Recognition, etc
                        data_labeler = dp.DataLabeler(labeler_type='unstructured')
                        data_labeler.set_params({ 'postprocessor': { 'output_format':'ner', 'use_word_level_argmax':True } })
                        model_predictions = data_labeler.predict(data, predict_options=dict(show_confidences=True))

                        redacted_list = list(text) 
                        for pred in model_predictions['pred'][0]:
                            if pred[2] in opts['redaction-topics']:
                                for i in range(pred[0], pred[1]):
                                    redacted_list[i] = opts['redaction-character']
                        redacted_text = "".join(redacted_list)

                        # save this as an attachment to the vCon
                        adapter_meta= {}
                        adapter_meta['src'] = 'conserver'
                        adapter_meta['type'] = 'redaction'
                        adapter_meta['data'] = redacted_text
                        vCon.attachments.append(adapter_meta)
                    await r.set("vcon-{}".format(vCon.uuid), vCon.dumps())


                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("transcription plugin: error: {}".format(e))


    except asyncio.CancelledError:
        logger.debug("transcription Cancelled")

    logger.info("transcription stopped")    



