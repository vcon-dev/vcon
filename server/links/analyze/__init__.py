from lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import logging
import openai
import json
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    RetryError,
)  # for exponential backoff
from lib.metrics import init_metrics, stats_gauge, stats_count
import time
from lib.links.filters import is_included, randomly_execute_with_sampling

init_metrics()

logger = init_logger(__name__)

default_options = {
    "prompt": "Summarize this transcript in a few sentences.",
    "analysis_type": "summary",
    "model": "gpt-3.5-turbo-16k",
    "sampling_rate": 1,
    "temperature": 0,
    "source": {
        "analysis_type": "transcript",
        "text_location": "body.paragraphs.transcript",
    },
}


def get_analysys_for_type(vcon, index, analysis_type):
    for a in vcon.analysis:
        if a["dialog"] == index and a["type"] == analysis_type:
            return a
    return None


@retry(
    wait=wait_exponential(multiplier=2, min=1, max=65),
    stop=stop_after_attempt(6),
    before_sleep=before_sleep_log(logger, logging.INFO),
)
def generate_analysis(transcript, prompt, model, temperature) -> str:
    # logger.info(f"TRANSCRIPT: {transcript}")
    # logger.info(f"PROMPT: {prompt}")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt + "\n\n" + transcript},
    ]
    # logger.info(f"messages: {messages}")
    # logger.info(f"MODEL: {model}")

    sentiment_result = openai.ChatCompletion.create(
        model=model, messages=messages, temperature=temperature
    )
    return sentiment_result["choices"][0]["message"]["content"]


def run(
    vcon_uuid,
    link_name,
    opts=default_options,
):
    module_name = __name__.split(".")[-1]
    logger.info(f"Starting {module_name}: {link_name} plugin for: {vcon_uuid}")
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts

    vcon_redis = VconRedis()
    vCon = vcon_redis.get_vcon(vcon_uuid)

    if not is_included(opts, vCon):
        logger.info(f"Skipping {link_name} vCon {vcon_uuid} due to filters")
        return vcon_uuid

    if not randomly_execute_with_sampling(opts):
        logger.info(f"Skipping {link_name} vCon {vcon_uuid} due to sampling")
        return vcon_uuid

    openai.api_key = opts["OPENAI_API_KEY"]
    openai.max_retries = 0
    openai.timeout = 120.0

    source_type = navigate_dict(opts, "source.analysis_type")
    text_location = navigate_dict(opts, "source.text_location")

    for index, dialog in enumerate(vCon.dialog):
        source = get_analysys_for_type(vCon, index, source_type)
        if not source:
            logger.warning("No %s found for vCon: %s", source_type, vCon.uuid)
            continue
        source_text = navigate_dict(source, text_location)
        if not source_text:
            logger.warning(
                "No source_text found at %s for vCon: %s", text_location, vCon.uuid
            )
            continue
        analysis = get_analysys_for_type(vCon, index, opts["analysis_type"])

        # See if it already has the analysis
        if analysis:
            logger.info(
                "Dialog %s already has a %s in vCon: %s",
                index,
                opts["analysis_type"],
                vCon.uuid,
            )
            continue

        logger.info(
            "Analysing dialog %s with options: %s",
            index,
            {k: v for k, v in opts.items() if k != "OPENAI_API_KEY"},
        )
        try:
            start = time.time()
            analysis = generate_analysis(
                transcript=source_text,
                prompt=opts["prompt"],
                model=opts["model"],
                temperature=opts["temperature"],
            )
            stats_gauge(
                "conserver.link.openai.analysis_time",
                time.time() - start,
                tags=[f"analysis_type:{opts['analysis_type']}"],
            )
        except (RetryError, Exception) as e:
            logger.error(
                "Failed to generate analysis for vCon %s after multiple retries: %s",
                vcon_uuid,
                e,
            )
            stats_count(
                "conserver.link.openai.analysis_failures",
                tags=[f"analysis_type:{opts['analysis_type']}"],
            )
            break
        vendor_schema = {}
        vendor_schema["model"] = opts["model"]
        vendor_schema["prompt"] = opts["prompt"]
        vCon.add_analysis(
            type=opts["analysis_type"],
            dialog=index,
            vendor="openai",
            body=analysis,
            encoding="none",
            extra={
                "vendor_schema": vendor_schema,
            },
        )
    vcon_redis.store_vcon(vCon)
    logger.info(f"Finished analyze - {module_name}:{link_name} plugin for: {vcon_uuid}")

    return vcon_uuid


def navigate_dict(dictionary, path):
    keys = path.split(".")
    current = dictionary
    for key in keys:
        if key in current:
            current = current[key]
        else:
            return None
    return current
