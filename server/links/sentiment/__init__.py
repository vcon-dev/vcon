from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import openai

logger = init_logger(__name__)

default_options = {
    "prompt": "Summarize this conversation: ",
}


def get_transcription(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a['type'] == 'transcript':
            return a
    return None


def get_summary(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a['type'] == 'summary':
            return a
    return None


def get_customer_issue(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a['type'] == 'customer_issue':
            return a
    return None


def find_customer_issue(summary):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "If there were any communication issues, frustrations, anger or dissapointment, respond with only the words 'NEEDS REVIEW', otherwise respond 'NO REVIEW NEEDED"},
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
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts
    logger.info("Starting sentiment plugin for: %s", vcon_uuid)
    openai.api_key = opts["OPENAI_API_KEY"]
    # Cannot create redis client in global context as it will wait on async event
    # loop which may go away.
    vcon_redis = VconRedis()
    vCon = await vcon_redis.get_vcon(vcon_uuid)

    for index, dialog in enumerate(vCon.dialog):
        summary = get_summary(vCon , index)
        if not summary:
            logger.info("No summary found for vcon: %s", vCon.uuid)
            continue

        customer_issue = get_customer_issue(vCon , index)
        if customer_issue:
            logger.info("There's a customer_issue already for vCon: %s", vCon.uuid)
            continue

        customer_issue = find_customer_issue(summary["body"])
        logger.info("Checked customer_sentiment: %s", vCon.uuid)
        vCon.add_analysis_transcript(
            index, customer_issue, "openai", analysis_type="customer_issue"
        )
    await vcon_redis.store_vcon(vCon)

    # Return the vcon_uuid down the chain.
    # If you want the vCon processing to stop (if you are filtering them, for instance)
    # send None
    return vcon_uuid
