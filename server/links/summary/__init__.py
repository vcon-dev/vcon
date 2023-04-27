from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import openai
import os
from settings import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

logger = init_logger(__name__)

default_options = {
    "prompt": "Summarize this conversation: ",
}

async def run(
    vcon_uuid,
    opts=default_options,
):
    logger.debug("Starting vcon summary")
    # Cannot create redis client in global context as it will wait on async event
    # loop which may go away.
    vcon_redis = VconRedis()
    vCon = await vcon_redis.get_vcon(vcon_uuid)

    # Find the transcript, if it exists.
    for analysis in vCon.analysis:
        if analysis['type'] == 'script':
            script = analysis['body']
            robot_prompt = opts['prompt'] + script
            summarize_result = openai.Completion.create(
                model="text-davinci-003",
                prompt=robot_prompt,
                max_tokens=1000,
                temperature=0
                )
            summary = summarize_result["choices"][0]["text"]                
            vCon.add_analysis(analysis['dialog'], 'summary', summary, 'openai', opts['prompt'])
    await vcon_redis.store_vcon(vCon)

    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid
