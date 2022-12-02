import asyncio
import redis.asyncio as redis
import json
import asyncio
import logging
from settings import LOG_LEVEL, REDIS_URL
from redis.commands.json.path import Path
import traceback
from .models import CallLogs


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

default_options = {
    "name": "postgres",
    "ingress-topics": [],
    "egress-topics":[],
    "transcribe": True,
    "min_transcription_length": 10,
    "deepgram": False,
}
options = {}

async def start(opts=default_options):
    logger.info("Starting the posgres plugin!!!")
    while True:
        try:
            r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
            p = r.pubsub(ignore_subscribe_messages=True)
            await p.subscribe(*opts['ingress-topics'])
            async for message in p.listen():
                vConUuid = message['data']
                logger.info("postgres plugin: received vCon: %s", vConUuid)
                vcon_dict = await r.json().get(f"vcon:{vConUuid}")
                logger.info("The vCon in postgres %s", vcon_dict)
                payload = vcon_dict["attachments"][0]["payload"]
                projection = vcon_dict["attachments"][1]
                call_log_id = payload["id"]
                CallLogs.create(
                    id = call_log_id,
                    agent_extension = projection["extension"],
                    # agent_cxm_id = CharField(null=True),
                    # agent_cached_details = BinaryJSONField(null=True),
                    dealer_number = projection["dealer_number"],
                    # dealer_cxm_id = CharField(null=True),
                    # dealer_cached_details = BinaryJSONField(null=True),
                    customer_number = projection["customer_number"],
                    direction = payload["direction"],
                    # disposition = CharField(null=True),
                    s3_key = f"{call_log_id}.wav",
                    # call_started_on = projection["call_started_on"],
                    duration = projection["duration"],
                    # transcript = CharField(null=True),
                    # created_on = projection["created_on"],
                    # modified_on = projection["modified_on"],
                    # json_version = CharField(null=True),
                    # cdr_json = BinaryJSONField(null=True),
                )
                logger.info("Call log added successfully")
                # TODO get projection from attachment and save it to Postgres.

                for topic in opts['egress-topics']:
                    await r.publish(topic, vConUuid)

        except asyncio.CancelledError:
            logger.debug("posgres plugin Cancelled")
            break
        except Exception:
            logger.error("posgres plugin: error: \n%s", traceback.format_exc())
            logger.error("Shoot!")
    logger.info("posgres plugin stopped")



