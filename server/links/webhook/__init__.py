from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger

import aiohttp
import json

logger = init_logger(__name__)

default_options = {
    "webhook-urls": ["https://eo91qivu6evxsty.m.pipedream.net"],
}


async def run(
    vcon_uuid,
    link_name,
    opts=default_options,
):
    logger.debug("Starting transcribe::run")
    # Cannot create redis client in global context as it will get created on async
    # event loop which may go away.
    vcon_redis = VconRedis()
    vCon = await vcon_redis.get_vcon(vcon_uuid)

    # The webhook needs a stringified JSON version.
    json_vCon = vCon.dumps()
    json_dict = json.loads(json_vCon)

    # Post this to each webhook url
    for url in opts["webhook-urls"]:
        async with aiohttp.ClientSession() as session:
            logger.info(
                f"webhook plugin: posting vcon {vcon_uuid} to webhook url: {url}"
            )
            async with session.post(url, json=json_dict) as resp:
                logger.info(
                    f"webhook plugin response for {vcon_uuid}: {resp.status} {await resp.text()}"
                )
    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid
