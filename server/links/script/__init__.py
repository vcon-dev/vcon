from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import openai
from settings import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

logger = init_logger(__name__)

default_options = {
    "prompt": "Rewrite this transcript into speakers, speaking like they are from Boston : ",
}


def run(
    vcon_uuid,
    link_name,
    opts=default_options,
):
    logger.debug("Starting script::run")

    vcon_redis = VconRedis()
    vCon = vcon_redis.get_vcon(vcon_uuid)

    # Find the transcript, if it exists.
    for analysis in vCon.analysis:
        if analysis["type"] == "transcript" and analysis["vendor"] != "Whisper":
            # Raise an exception
            logger.error(f"unsupported vendor {analysis['vendor']} for transcript")
            return None

        if analysis["type"] != "transcript":
            continue

        transcript = analysis["body"]["ori_dict"]["text"]
        try:
            # This can fail if the transcript is too long.
            robot_prompt = opts["prompt"] + transcript
            rewrite_result = openai.Completion.create(
                model="text-davinci-003",
                prompt=robot_prompt,
                max_tokens=2000,
                temperature=0,
            )
            script = rewrite_result["choices"][0]["text"]
        except Exception as ex:
            log_traceback(ex)  # noqa F821
            script = transcript
        # TODO: Add new mime type for script (text/plain)
        vCon.add_analysis(
            analysis["dialog"], "script", script, "openai", opts["prompt"]
        )

    vcon_redis.store_vcon(vCon)

    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid
