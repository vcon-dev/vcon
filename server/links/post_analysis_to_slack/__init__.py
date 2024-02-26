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
    "only_if": {"analysis_type": "customer_frustration", "includes": "NEEDS REVIEW"},
}


def get_team(vcon):
    team_name = None
    for a in vcon.attachments:
        if a["type"] == "strolid_dealer":
            t_obj = json.loads(a["body"])
            team = t_obj.get("team", None)
            if team:
                team_name = team["name"]
                team_name = team_name.split()[0].lower()
    return team_name


def get_dealer(vcon):
    dealer = None
    for a in vcon.attachments:
        if a["type"] == "strolid_dealer":
            d_obj = json.loads(a["body"])
            dealer = d_obj.get("name", None)
    return dealer


def get_summary(vcon, index):
    for a in vcon.analysis:
        if a["dialog"] == index and a["type"] == "summary":
            return a
    return None


def post_blocks_to_channel(token, channel_name, abstract, url, opts):
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Check this out :neutral_face:"},
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": abstract}},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Please review the details here:"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Details", "emoji": True},
                "value": "click_me_123",
                "url": url,
                "action_id": "button-action",
            },
        },
    ]
    client = WebClient(token=token)
    try:
        client.chat_postMessage(channel=channel_name, blocks=blocks, text=abstract)
    except Exception as e:
        # Code to run if an exception is raised
        client.chat_postMessage(
            channel=opts["default_channel_name"],
            text=f"The channel name doesn't exist - {channel_name}",
        )
        logger.error(f"An error occurred posting to {channel_name}: {e}")


async def run(vcon_id, link_name, opts=default_options):
    module_name = __name__.split(".")[-1]
    logger.info(f"Starting {module_name} plugin for: {vcon_id}")
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts
    propogate_to_next_link = True

    # Cannot create redis client in global context as it will wait on async event
    # loop which may go away.
    vcon_redis = VconRedis()
    vcon = await vcon_redis.get_vcon(vcon_id)

    for a in vcon.analysis:
        # we still need to run this check give the following scenario:
        # 0 customers_frustration None
        # 1 customer_frustration Needs Review
        # we need to skip first one an only post the second one to slack
        if a["type"] != opts["only_if"]["analysis_type"]:
            continue
        if opts["only_if"]["includes"] not in a["body"]:
            continue
        if a.get("was_posted_to_slack"):
            continue

        # TODO use our lib.links.filters.is_included instead of this

        url = f"{opts['url']}?_vcon_id=\"{vcon.uuid}\""
        team_name = get_team(vcon)
        dealer_name = get_dealer(vcon)
        summary = get_summary(vcon, a["dialog"])
        abstract = summary["body"]

        if team_name and team_name != "strolid":
            channel_name = f"team-{team_name}-alerts"
            abstract = abstract + f" #{dealer_name}"
            post_blocks_to_channel(opts["token"], channel_name, abstract, url, opts)

        post_blocks_to_channel(
            opts["token"], opts["default_channel_name"], abstract, url, opts
        )
        a["was_posted_to_slack"] = True

    await vcon_redis.store_vcon(vcon)

    if propogate_to_next_link:
        return vcon_id  #
