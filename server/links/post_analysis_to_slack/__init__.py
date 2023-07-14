from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import json
from slack_sdk.web import WebClient

logger = init_logger(__name__)

default_options = {
    "token": None,
    "channel_name": None,
    "url": "Url to hex sheet",
    "analysis_to_post": "summary",
    "only_if": {
        "analysis_type": "customer_frustration",
        "includes": "NEEDS REVIEW"
    }
}


def get_team(vcon):
    team_name = "rainbow"
    for a in vcon.attachments:
        if a['type'] == 'strolid_dealer':
            t_obj = json.loads(a['body'])
            team = t_obj.get('team', None)
            if team:
                team_name = t_obj['name']
    return team_name


def get_summary(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a['type'] == 'summary':
            return a
    return None


def post_blocks_to_channel(token, channel_name, abstract, url):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Check this out :neutral_face:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": abstract 
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Please review the details here:"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Details",
                    "emoji": True
                },
                "value": "click_me_123",
                "url": url,
                "action_id": "button-action"
            }
        }
    ]
    client = WebClient(token=token)
    try:
        client.chat_postMessage(
            channel=channel_name,
            blocks=blocks,
            text=abstract
        )
    except Exception as e:
        # Code to run if an exception is raised
        logger.error(f"An error occurred posting to {channel_name}: {e}")


async def run(
    vcon_id,
    opts=default_options
):
    link_name = __name__.split(".")[-1]
    logger.info(f"Starting {link_name} plugin for: {vcon_id}")
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts
    propogate_to_next_link = True

    # Cannot create redis client in global context as it will wait on async event
    # loop which may go away.
    vcon_redis = VconRedis()
    vcon = await vcon_redis.get_vcon(vcon_id)

    for a in vcon.analysis:
        if a['type'] != opts["only_if"]["analysis_type"]:
            continue
        if opts["only_if"]["includes"] not in a['body']:
            continue
        if a.get('was_posted_to_slack'):
            continue

        url = f"{opts['url']}?_vcon_id=\"{vcon.uuid}\""
        team_name = get_team(vcon)
        summary = get_summary(vcon, a['dialog'])
        summary_text = summary['body']
        abstract = summary_text + f" #{team_name}"
        post_blocks_to_channel(opts['token'], opts['channel_name'], abstract, url)
        a['was_posted_to_slack'] = True

    await vcon_redis.store_vcon(vcon)

    if propogate_to_next_link:
        return vcon_id

