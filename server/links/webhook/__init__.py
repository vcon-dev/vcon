from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
vcon_redis = VconRedis()
logger = init_logger(__name__)
import aiohttp

default_options = {
    "webhook-urls": ["https://eo91qivu6evxsty.m.pipedream.net"],
}

async def run(
    vcon_uuid,
    opts=default_options,
):
    logger.debug("Starting transcribe::run")
    vCon = await vcon_redis.get_vcon(vcon_uuid)

    # The webhook needs a stringified JSON version. 
    json_vCon = vCon.dumps()
    
    # Post this to each webhook url
    for url in opts["webhook-urls"]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=json_vCon) as resp:
                logger.debug("webhook plugin: posted to webhook url: {}".format(url))
                logger.debug("webhook plugin: response: {}".format(resp.status))
    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid