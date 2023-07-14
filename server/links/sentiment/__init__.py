from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import openai

logger = init_logger(__name__)

default_options = {
    "prompt": "If there were any communication issues, frustrations, anger or dissapointment, respond with only the words 'NEEDS REVIEW', otherwise respond 'NO REVIEW NEEDED'",
    "analysis_type": "sentiment",
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


def generate_analysis(summary, prompt):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": summary}
    ]
    sentiment_result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
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
        # TODO ask Thomas why we user summary insted of transcript
        summary = get_analysys_for_type(vCon , index, "summary")
        if not summary:
            logger.info("No summary found for vcon: %s", vCon.uuid)
            continue

        analysis = get_analysys_for_type(vCon , index, opts["analysis_type"])
        if analysis:
            logger.info("There's a analysis type %s already for vCon: %s", opts["analysis_type"], vCon.uuid)
            continue

        analysis = generate_analysis(summary["body"], opts["prompt"])
        vCon.add_analysis_transcript(
            index, analysis, "openai", analysis_type=opts["analysis_type"]
        )

        # if opts["filter"] and opts["filter"] not in sentiment:
        #     logger.info("Filtered out because of sentiment filter: %s", vCon.uuid)
        #     propogate_to_next_link = False

    await vcon_redis.store_vcon(vCon)

    if propogate_to_next_link:
        return vcon_uuid
