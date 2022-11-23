import asyncio
import async_timeout
import redis.asyncio as redis
import json
import asyncio
import boto3
from settings import AWS_KEY_ID, AWS_SECRET_KEY, AWS_BUCKET
import logging

from settings import LOG_LEVEL
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

default_options = {
    "name": "s3",
    "ingress-topics": ["ingress-vcons"],
    "egress-topics":[],
    "AWS_KEY_ID": AWS_KEY_ID,
    "AWS_SECRET_KEY": AWS_SECRET_KEY,
    "AWS_BUCKET": AWS_BUCKET,
    "S3Path": "plugins/call_log/"
}
options = {}

async def start(opts=default_options):
    logger.info("Starting the s3 storage plugin")

    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message['data'].decode('utf-8')
                    logger.info("S3: received vCon: {}".format(vConUuid))
                    body = await r.get("vcon:{}".format(str(vConUuid)))

                    # Save the vCon to S3
                    s3 = boto3.resource(
                        's3',
                        region_name='us-east-1',
                        aws_access_key_id=opts["AWS_KEY_ID"],
                        aws_secret_access_key=opts["AWS_SECRET_KEY"]
                        )
                    
                    S3Path = opts['S3Path'] + vConUuid + ".vcon"
                    s3.Bucket(opts["AWS_BUCKET"]).put_object(Key=S3Path, Body=body)
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.debug("S3 adapter error: {}".format(e))

    except asyncio.CancelledError:
        logger.debug("s3 storage plugin Cancelled")

    logger.info("s3 storage plugin stopped")    