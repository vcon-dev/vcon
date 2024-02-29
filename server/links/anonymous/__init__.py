from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import openai

logger = init_logger(__name__)

default_options = {
    "prompt": "Anonymize this conversation, using friendly names: ",
}


def run(
    vcon_uuid,
    link_name,
    opts=default_options,
):
    logger.debug("Starting anonymous")

    vcon_redis = VconRedis()
    vCon = vcon_redis.get_vcon(vcon_uuid)

    # Find the transcript, if it exists.
    for analysis in vCon.analysis:
        if analysis["type"] == "script":
            script = analysis["body"]
            robot_prompt = opts["prompt"] + script
            try:
                summarize_result = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=robot_prompt,
                    max_tokens=2000,
                    temperature=0,
                )
            except Exception as e:
                logger.error(f"Error in OpenAI: {e}")
                continue

            anonymous = summarize_result["choices"][0]["text"]
            vCon.add_analysis(
                analysis["dialog"], "anonymous", anonymous, "openai", opts["prompt"]
            )

    vcon_redis.store_vcon(vCon)

    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid
