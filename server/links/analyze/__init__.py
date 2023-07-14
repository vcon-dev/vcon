from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import openai

logger = init_logger(__name__)

default_options = {
    "prompt": "Summarize this transcript in a few sentences, then indicate if they customer was frustrated or not, and if agent was helpful?",
    "analysis_type": "summary",
    "model": "gpt-4"
}


def get_transcription(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a['type'] == 'transcript':
            return a
    return None


def get_analysys_for_type(vcon, index, analysis_type):
    for a in vcon.analysis:
        if a["dialog"] == index and a['type'] == analysis_type:
            return a
    return None


def generate_analysis(transcript, prompt, model):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": transcript}
    ]
    sentiment_result = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )
    return sentiment_result["choices"][0]["message"]["content"]


async def run(
    vcon_uuid,
    opts=default_options,
):
    link_name = __name__.split(".")[-1]
    logger.info(f"Starting {link_name} plugin for: {vcon_uuid}")
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts
    propogate_to_next_link = True
    # Cannot create redis client in global context as it will wait on async event
    # loop which may go away.
    vcon_redis = VconRedis()
    vCon = await vcon_redis.get_vcon(vcon_uuid)

    openai.api_key = opts["OPENAI_API_KEY"]

    for index, dialog in enumerate(vCon.dialog):
        transcription = get_transcription(vCon, index)
        if not transcription:
            logger.info("No transcript found for vCon: %s", vCon.uuid)
            continue

        transcription_text = transcription['body']['transcript']
        analysis = get_analysys_for_type(vCon , index, opts["analysis_type"])
        # See if it already has summary
        if analysis:
            logger.info("Dialog %s already summarized in vCon: %s", index, vCon.uuid)
            continue
        analysis = generate_analysis(transcription_text, opts["prompt"], opts["model"])
        vCon.add_analysis_transcript(
            index, analysis, "openai", analysis_type=opts["analysis_type"]
        )
    await vcon_redis.store_vcon(vCon)

    if propogate_to_next_link:
        return vcon_uuid
