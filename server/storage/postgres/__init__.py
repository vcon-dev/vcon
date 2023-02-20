import asyncio
import traceback

import copy
import redis.asyncio as redis
from lib.logging_utils import init_logger
from lib.sentry import init_sentry
from settings import REDIS_URL

from server.lib.vcon_redis import VconRedis

from .models import CallLogs

init_sentry()

logger = init_logger(__name__)


default_options = {
    "name": "postgres",
    "ingress-topics": [],
    "egress-topics": [],
    "transcribe": True,
    "min_transcription_length": 10,
    "deepgram": False,
}
options = {}


async def start(opts=None):
    if opts is None:
        opts = copy.deepcopy(default_options)
    logger.info("Starting the posgres plugin!!!")
    while True:
        try:
            r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
            vcon_redis = VconRedis(redis_client=r)
            p = r.pubsub(ignore_subscribe_messages=True)
            await p.subscribe(*opts["ingress-topics"])
            async for message in p.listen():
                vConUuid = message["data"]
                logger.info("postgres plugin: received vCon: %s", vConUuid)
                vCon = await vcon_redis.get_vcon(vConUuid)
                projection = None
                for attachment in vCon.attachments:
                    if attachment.get("projection") == "call_log":
                        projection = attachment
                        break
                if projection:
                    CallLogs.insert(
                        id=projection.get("id"),
                        agent_extension=projection.get("extension"),
                        # agent_cxm_id = CharField(null=True),
                        agent_cached_details={"name": projection.get("agent_name")},
                        dealer_number=projection.get("dealer_number"),
                        dealer_cxm_id=projection.get("dealer_cxm_id"),
                        dealer_cached_details=projection.get("dealer_cached_details"),
                        customer_number=projection.get("customer_number"),
                        direction=projection.get("direction"),
                        disposition=projection.get("disposition"),
                        # s3_key = projection.get("s3_key"),
                        call_started_on=projection.get("call_started_on"),
                        duration=projection.get("duration"),
                        dialog_json=projection.get("dialog"),
                        # transcript = CharField(null=True),
                        created_on=projection["created_on"],
                        modified_on=projection["modified_on"],
                        # json_version = CharField(null=True),
                        # cdr_json = BinaryJSONField(null=True),
                        source="bria",
                    ).on_conflict(
                        action="update",
                        preserve=[
                            "agent_extension",
                            "agent_cached_details",
                            "disposition",
                            "duration",
                            "dialog_json",
                            "modified_on",
                            "dealer_cxm_id",
                            "dealer_cached_details",
                            "dealer_number",
                        ],
                        conflict_target=[CallLogs.id],
                    ).execute()
                    logger.info("Call log added successfully")
                    # TODO get projection from attachment and save it to Postgres.

                    for topic in opts["egress-topics"]:
                        await r.publish(topic, vConUuid)

        except asyncio.CancelledError:
            logger.debug("posgres plugin Cancelled")
            break
        except Exception:
            logger.error("posgres plugin: error: \n%s", traceback.format_exc())
            logger.error("Shoot!")
    logger.info("posgres plugin stopped")
