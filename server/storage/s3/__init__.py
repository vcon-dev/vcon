import redis.asyncio as redis
from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import boto3
from settings import AWS_KEY_ID, AWS_SECRET_KEY, AWS_BUCKET
vcon_redis = VconRedis()
logger = init_logger(__name__)

logger = init_logger(__name__)


default_options = {
    "name": "s3",
    "AWS_KEY_ID": AWS_KEY_ID,
    "AWS_SECRET_KEY": AWS_SECRET_KEY,
    "AWS_BUCKET": AWS_BUCKET,
    "S3Path": "",
}


async def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the S3 storage")
    try:
        vcon = await vcon_redis.get_vcon(vcon_uuid)
        s3 = boto3.client(
            "s3",
            aws_access_key_id=opts['AWS_KEY_ID'],
            aws_secret_access_key=opts['AWS_SECRET_KEY']
        )
        s3.put_object(
            Bucket=opts['AWS_BUCKET'],
            Key=f"{opts['S3Path']}/{vcon_uuid}",
            Body=vcon.dumps()
        )
        logger.info(f"s3 storage plugin: inserted vCon: {vcon_uuid}")   
    except Exception as e:
        logger.error(f"s3 storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ")
        raise e
    