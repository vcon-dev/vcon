from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger


logger = init_logger(__name__)

default_options = {
    "name": "transcription",
    "transcribe_options": {"model_size": "base", "output_options": ["vendor"]},
}


def run(
    vcon_uuid,
    link_name,
    opts=default_options,
):
    logger.debug("Starting transcribe::run")

    vcon_redis = VconRedis()
    vCon = vcon_redis.get_vcon(vcon_uuid)
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
        vcon_redis.store_vcon(vCon)

    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid
