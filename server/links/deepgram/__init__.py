from typing import Optional
from lib.logging_utils import init_logger
import logging
from deepgram import DeepgramClient, PrerecordedOptions
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    RetryError,
    before_sleep_log,
)  # for exponential backoff
from server.lib.vcon_redis import VconRedis
import json
from lib.error_tracking import init_error_tracker
from lib.metrics import init_metrics, stats_gauge, stats_count
import time

init_error_tracker()
init_metrics()
logger = init_logger(__name__)

default_options = {"minimum_duration": 60, "DEEPGRAM_KEY": None}


def get_transcription(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a["type"] == "transcript":
            return a
    return None


@retry(
    wait=wait_exponential(
        multiplier=2, min=1, max=65
    ),  # Will wait 1 then 2 then 4 then ....32 seconds.  All the retries together will take less than 65 seconds.
    stop=stop_after_attempt(6),
    before_sleep=before_sleep_log(logger, logging.INFO),
)
def transcribe_dg(dg_client, dialog, opts) -> Optional[dict]:
    url = dialog["url"]
    source = {"url": url}
    options = PrerecordedOptions(**opts)
    url_response = dg_client.listen.prerecorded.v("1").transcribe_url(source, options)
    response = json.loads(url_response.to_json())

    alternatives = response["results"]["channels"][0]["alternatives"]
    detected_language = response["results"]["channels"][0]["detected_language"]
    transcript = alternatives[0]
    transcript["detected_language"] = detected_language
    return transcript


def run(
    vcon_uuid,
    link_name,
    opts=default_options,
):
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts

    logger.info("Starting deepgram plugin for vCon: %s", vcon_uuid)

    vcon_redis = VconRedis()
    vCon = vcon_redis.get_vcon(vcon_uuid)

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

        dg_client = DeepgramClient(opts["DEEPGRAM_KEY"])
        try:
            start = time.time()
            result = transcribe_dg(dg_client, dialog, opts["api"])
            stats_gauge(
                "conserver.link.deepgram.transcription_time", time.time() - start
            )
        except (RetryError, Exception) as e:
            logger.error(
                "Failed to transcribe vCon %s after multiple retries: %s", vcon_uuid, e
            )
            stats_count("conserver.link.deepgram.transcription_failures")
            break

        if not result:
            logger.warning("No transcription generated for vCon %s", vcon_uuid)
            stats_count("conserver.link.deepgram.transcription_failures")
            break

        # send the confidence to datadog for monitoring purposes (we can graph it) and alerting
        stats_gauge("conserver.link.deepgram.confidence", result["confidence"])

        # If the confidence is too low, don't store the transcript since it probably garbage
        if result["confidence"] < 0.5:
            logger.warning(
                "Low confidence result for vCon %s: %s", vcon_uuid, result["confidence"]
            )
            stats_count("conserver.link.deepgram.transcription_failures")
            break

        logger.info("Transcribed vCon: %s", vCon.uuid)

        vendor_schema = {}
        # Remove credentials from vendor_schema
        vendor_schema["opts"] = {k: v for k, v in opts.items() if k != "DEEPGRAM_KEY"}

        vCon.add_analysis(
            type="transcript",
            dialog=index,
            vendor="deepgram",
            body=result,
            extra={
                "vendor_schema": vendor_schema,
            },
        )
    vcon_redis.store_vcon(vCon)

    # Forward the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them out, for instance)
    # send None
    logger.info("Finished deepgram plugin for vCon: %s", vcon_uuid)
    return vcon_uuid
