from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger


logger = init_logger(__name__)

default_options = {
    "name": "transcription",
    "transcribe_options": {"model_size": "base", "output_options": ["vendor"]},
}


async def run(
    vcon_uuid,
    link_name,
    opts=default_options,
):
    logger.debug("Starting transcribe::run")
    # Cannot create the redis client in the global context as it will wait on async
    # event loop which may go away.
    vcon_redis = VconRedis()
    vCon = await vcon_redis.get_vcon(vcon_uuid)
    original_analysis_count = len(vCon.analysis)
    annotated_vcon = vCon.transcribe(**opts["transcribe_options"])
    new_analysis_count = len(annotated_vcon.analysis)
    logger.debug(
        "transcribe plugin: vCon: {} analysis was: {} now: {}".format(
            vcon_uuid, original_analysis_count, new_analysis_count
        )
    )
    # If we added any analysis, save it
    if new_analysis_count != original_analysis_count:
        await vcon_redis.store_vcon(vCon)

    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid
