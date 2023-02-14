import asyncio
import copy
import traceback
import boto3
import redis.asyncio as redis
from lib.logging_utils import init_logger
from settings import AWS_BUCKET, AWS_KEY_ID, AWS_SECRET_KEY, REDIS_URL
from server.lib.vcon_redis import VconRedis

logger = init_logger(__name__)


default_options = {
    "name": "s3",
    "ingress-topics": [],
    "egress-topics": [],
    "AWS_KEY_ID": AWS_KEY_ID,
    "AWS_SECRET_KEY": AWS_SECRET_KEY,
    "AWS_BUCKET": AWS_BUCKET,
    "S3Path": "",
}


async def start(opts=None):
    if opts is None:
        opts = copy.deepcopy(default_options)
    logger.info("Starting the s3 storage plugin")
    while True:
        try:
            r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
            vcon_redis = VconRedis(redis_client=r)
            p = r.pubsub(ignore_subscribe_messages=True)
            await p.subscribe(*opts["ingress-topics"])
            async for message in p.listen():
                vConUuid = message["data"]
                logger.info(f"S3: received vCon: {vConUuid}")
                vCon = await vcon_redis.get_vcon(vConUuid)

                # Save the vCon to S3
                s3 = boto3.resource(
                    "s3",
                    region_name="us-east-1",
                    aws_access_key_id=opts["AWS_KEY_ID"],
                    aws_secret_access_key=opts["AWS_SECRET_KEY"],
                )

                S3Path = opts["S3Path"] + vConUuid + ".vcon"
                s3.Bucket(opts["AWS_BUCKET"]).put_object(Key=S3Path, Body=vCon.dumps())
                for topic in opts["egress-topics"]:
                    await r.publish(topic, vConUuid)
        except asyncio.CancelledError:
            logger.debug("s3 storage plugin Cancelled")
            break
        except Exception:
            logger.error("s3 storage plugin: error: \n%s", traceback.format_exc())
            logger.error("Shoot!")

    logger.info("s3 storage plugin stopped")
