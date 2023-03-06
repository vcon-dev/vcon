import redis.asyncio as redis
from redis.commands.json.path import Path
import asyncio
from lib.logging_utils import init_logger
import vcon
import simplejson as json
import time
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

logger = init_logger(__name__)

r = redis.Redis(host="localhost", port=6379, db=0)

default_options = {"name": "openai_summary", "ingress-topics": [], "egress-topics": []}
options = {}


async def run(
    vcon_uuid,
    opts=default_options,
):
    logger.info("openai_summary plugin: processing vCon: {}".format(vcon_uuid))
    inbound_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())
    vCon = vcon.Vcon()
    vCon.loads(json.dumps(inbound_vcon))
    for index, analysis in enumerate(vCon.analysis):
        if analysis["type"] == "transcript":
            logger.info("openai_summary plugin: processing vCon: {}".format(vcon_uuid))
            try:
                response = openai.Completion.create(
                    model="text-davinci-003",
                    prompt="Please summarize the following : " + analysis["body"],
                    temperature=0.7,
                    max_tokens=256,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
            except Exception as e:
                logger.error("openai_summary plugin: error: {}".format(e))
                return None
            vCon.add_analysis_transcript(
                index, response.choices[0].text, "openai", analysis_type="summary"
            )

    # Remove the NAN
    try:
        str_vcon = vCon.dumps()
        json_vcon = json.loads(str_vcon)
        await r.json().set("vcon:{}".format(vCon.uuid), Path.root_path(), json_vcon)
        logger.info("openai_summary plugin: processed vCon: {}".format(vcon_uuid))
        return vcon_uuid
    except Exception as e:
        logger.error("openai_summary plugin: error: {}".format(e))
        return None


async def start(opts=default_options):
    logger.info("Starting the openai_summary plugin")
    try:
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts["ingress-topics"])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message["data"].decode("utf-8")
                    logger.info(
                        "openai_summary plugin: received vCon: {}".format(vConUuid)
                    )
                    try:
                        # get the start time
                        st = time.time()
                        returnVconUuuid = await run(vConUuid, opts)
                        # get the end time
                        et = time.time()

                        # get the execution time
                        elapsed_time = et - st
                        logger.info(
                            f"openai_summary Execution time {elapsed_time} seconds"
                        )

                    except Exception as e:
                        logger.error(
                            "openai_summary plugin threw unhandled error: {}".format(e)
                        )
                        returnVconUuuid = None

                    if returnVconUuuid:
                        for topic in opts["egress-topics"]:
                            await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("openai_summary plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("openai_summary Cancelled")

    logger.info("openai_summary stopped")
