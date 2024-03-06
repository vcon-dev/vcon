from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
from datetime import datetime

logger = init_logger(__name__)

default_options = {
    "path": ".",
    "add_timestamp_to_filename": True,
    "filename": "vcon",
    "extension": "json",
}


def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Saving vCon to file storage")
    try:
        vcon_redis = VconRedis()
        vcon = vcon_redis.get_vcon(vcon_uuid)
        if opts["add_timestamp_to_filename"]:
            filename = (
                f"{opts['filename']}-{datetime.now().isoformat()}.{opts['extension']}"
            )
        else:
            filename = f"{opts['filename']}.{opts['extension']}"

        with open(f"{opts['path']}/{filename}", "w") as f:
            f.write(vcon.dumps())
        logger.info(f"file storage plugin: inserted vCon: {vcon_uuid}")
    except Exception as e:
        logger.error(
            f"file storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} "
        )
        raise e
