from typing import Optional
from lib.logging_utils import init_logger
from deepgram import Deepgram
import retry
from server.lib.vcon_redis import VconRedis
import json

logger = init_logger(__name__)

default_options = {"minimum_duration": 60, "DEEPGRAM_KEY": None}


def get_transcription(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a["type"] == "transcript":
            return a
    return None


@retry.retry(tries=3, delay=1, backoff=2)
async def transcribe_dg(dg_client, dialog, opts) -> Optional[dict]:
    url = dialog["url"]
    source = {"url": url}

    try:
        response = await dg_client.transcription.prerecorded(source, opts)
        alternatives = response["results"]["channels"][0]["alternatives"]
        detected_language = response["results"]["channels"][0]["detected_language"]
        transcript = alternatives[0]
        transcript["detected_language"] = detected_language
        return transcript
    except Exception:
        logger.exception("Transaction failed: %s, %s", source, opts)
        raise


async def run(
    vcon_uuid,
    opts=default_options,
):
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts

    logger.info("Starting deepgram plugin for vCon: %s", vcon_uuid)
    # Cannot create reids client in global context as redis clients get started on async
    # event loop which may go away.
    vcon_redis = VconRedis()
    vCon = await vcon_redis.get_vcon(vcon_uuid)

    for index, dialog in enumerate(vCon.dialog):
        if dialog["type"] != "recording":
            logger.info(
                "deepgram plugin: skipping non-recording dialog %s in vCon: %s",
                index,
                vCon.uuid,
            )
            continue

        if not dialog["url"]:
            logger.info(
                "deepgram plugin: skipping no URL dialog %s in vCon: %s",
                index,
                vCon.uuid,
            )
            continue

        if dialog["duration"] < opts["minimum_duration"]:
            logger.info(
                "Skipping short recording dialog %s in vCon: %s", index, vCon.uuid
            )
            continue

        # See if it was already transcibed
        if get_transcription(vCon, index):
            logger.info("Dialog %s already transcribed on vCon: %s", index, vCon.uuid)
            continue

        dg_client = Deepgram(opts["DEEPGRAM_KEY"])
        result = await transcribe_dg(dg_client, dialog, opts["api"])
        if not result:
            break

        logger.info("Transcribed vCon: %s", vCon.uuid)
        opts.pop("DEEPGRAM_KEY")
        vendor_schema = {}
        vendor_schema["opts"] = opts
        vCon.add_analysis_transcript(
            index,
            result,
            "deepgram",
            json.dumps(vendor_schema),
            analysis_type="transcript",
        )
    await vcon_redis.store_vcon(vCon)

    # Forward the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them out, for instance)
    # send None
    logger.info("Finished deepgram plugin for vCon: %s", vcon_uuid)
    return vcon_uuid
