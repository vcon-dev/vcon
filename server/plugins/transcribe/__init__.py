from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
from stable_whisper import load_model

logger = init_logger(__name__)
model = load_model("base")

default_options = {
    "name": "transcription",
    "ingress-topics": [],
    "egress-topics": [],
    "transcribe_options": 
        {"model_size": "base", 
         "output_options": ["vendor"]
        }
}
vcon_redis = VconRedis(redis_client=r)

async def run(
    vcon_uuid,
    opts=default_options,
):
    logger.debug("Starting transcribe::run")
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