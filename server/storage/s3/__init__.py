from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import boto3

logger = init_logger(__name__)


default_options = {}


async def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the S3 storage")
    try:
        # Cannot create redis client in global context as it can get blocked on async
        # event loop which may go away.
        vcon_redis = VconRedis()
        vcon = await vcon_redis.get_vcon(vcon_uuid)
        s3 = boto3.client(
            "s3",
            aws_access_key_id=opts['aws_access_key_id'],
            aws_secret_access_key=opts['aws_secret_access_key']
        )

        s3_path = opts.get('s3_path')
        key = vcon_uuid + ".vcon"
        if s3_path:
            key = s3_path + "/" + key
        s3.put_object(Bucket=opts["aws_bucket"], Key=key, Body=vcon.dumps())

        logger.info(f"s3 storage plugin: inserted vCon: {vcon_uuid}")   
    except Exception as e:
        logger.error(f"s3 storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ")
        raise e

