from typing import Optional
from lib.logging_utils import init_logger
from deepgram import Deepgram
import retry
from server.lib.vcon_redis import VconRedis

logger = init_logger(__name__)

default_options = {
    "minimum_duration": 60,
    "DEEPGRAM_KEY": None
}


def get_transcription(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a['type'] == 'transcription':
            return a
    return None


@retry.retry(tries=3, delay=1, backoff=2)
async def transcribe_dg(dg_client, dialog) -> Optional[dict]:
    url = dialog['url']
    source = {'url': url}
    logger.info(f"Source: {url}")

    options = {
        "model": "nova",
        "smart_format": True,
    }
    try:
        response = await dg_client.transcription.prerecorded(source, options)
        alternatives = response['results']['channels'][0]['alternatives']
        return alternatives[0]
    except Exception:
        logger.exception("Transaction failed: %s, %s", source, options)
        return None


async def run(
    vcon_uuid,
    opts=default_options,
):
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts
    
    logger.debug("Starting deepgram plugin")
    # Cannot create reids client in global context as redis clients get started on async
    # event loop which may go away.
    vcon_redis = VconRedis()
    vCon = await vcon_redis.get_vcon(vcon_uuid)

    for index, dialog in enumerate(vCon.dialog):
        if dialog["type"] != "recording":
            logger.debug(
                f"deepgram plugin: skipping non-recording dialog {index} in vCon: {vcon_uuid}"
            )
            continue
        
        if not dialog["url"]:
            logger.debug(
                f"deepgram plugin: skipping no URL dialog {index} in vCon: {vcon_uuid}"
            )
            continue

        if dialog["duration"] < opts["minimum_duration"]:
            logger.debug(
                f"deepgram plugin: skipping short recording dialog {index} in vCon: {vcon_uuid}"
            )
            continue

        # See if it was already transcibed
        if get_transcription(vCon, index):
            logger.debug("Dialog %s already transcribed", index)
            continue

        logger.info("deepgram plugin: processing vCon: {}".format(vcon_uuid))
        logger.info("Duration of recording: {}".format(dialog["duration"]))

        dg_client = Deepgram(opts["DEEPGRAM_KEY"])
        logger.info(f"DG KEY: {opts['DEEPGRAM_KEY']}")
        result = await transcribe_dg(dg_client, dialog)
        if not result:
            break
    
        print(vCon.uuid, " transcribed")

        vCon.add_analysis_transcript(
            index, result, "deepgram", analysis_type="transcript"
        )
    await vcon_redis.store_vcon(vCon)

    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid

