import vcon
from redis.commands.json.path import Path
import asyncio
from lib.logging_utils import init_logger
from settings import SLACK_TOKEN
import simplejson as json
import copy
from slack_sdk import WebClient
import server.redis_mgr

logger = init_logger(__name__)

default_options = {
    "name": "slack",
    "ingress-topics": [""],
    "egress-topics": [],
    "slack-channels": ["C03HLPKUCHM"],
    "transcription_only": True,
    "full_analysis": False,
    "slack_token": SLACK_TOKEN,
}
options = {}

header_block = {
    "type": "header",
    "block_id": "header",
    "text": {"type": "plain_text", "text": "", "emoji": True},
}
context_block = {
    "type": "context",
    "block_id": "context",
    "elements": [{"type": "plain_text", "text": "", "emoji": True}],
}
keywords_block = {
    "type": "section",
    "block_id": "keywords",
    "text": {"type": "mrkdwn", "text": ""},
}
transcription_block = {
    "type": "section",
    "block_id": "transcription",
    "text": {"type": "mrkdwn", "text": ""},
}
conversation_block = {
    "type": "section",
    "block_id": "conversation",
    "text": {"type": "mrkdwn", "text": ""},
}

summary_block = {
    "type": "section",
    "block_id": "summary",
    "text": {"type": "plain_text", "text": "", "emoji": True},
}
action_element = {
    "type": "button",
    "text": {"type": "plain_text", "text": "transcript", "emoji": True},
    "value": "click_me_123",
    "action_id": "actionId-0",
    "url": "https://www.google.com",
}

actions_block = {"type": "actions", "elements": []}

divider_block = {"type": "divider"}


async def run(
    vcon_uuid,
    opts=default_options,
):
    global header_block, divider_block, context_block, keywords_block, summary_block, actions_block, action_element

    r = server.redis_mgr.get_client()
    inbound_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())
    vCon = vcon.Vcon()
    vCon.loads(json.dumps(inbound_vcon))

    # Check if we have a transcription
    transcription = False
    for analysis in vCon.analysis:
        if analysis["type"] == "transcript":
            transcription = True

    # If we only want transcriptions and there is no transcription, return
    if opts["transcription_only"] and not transcription:
        return vcon_uuid

    # Grab the vCon data
    blocks = []
    calling_party = vCon.parties[0]
    called_party = vCon.parties[1]

    block = copy.deepcopy(header_block)
    block["text"]["text"] = f"{calling_party['tel']} called {called_party['tel']}"
    blocks.append(block)

    block = copy.deepcopy(context_block)
    block["elements"][0][
        "text"
    ] = f"Call started at {vCon.created_at}, ID : {vCon.uuid}"
    block["block_id"] = f"context-{vCon.uuid}"
    blocks.append(divider_block)
    blocks.append(block)

    blocks.append(divider_block)

    # Get the keywords
    a = vCon.analysis
    for analysis in a:
        if analysis["type"] == "summary":
            block = copy.deepcopy(summary_block)
            block["text"]["text"] = f"{analysis['body']}"
            blocks.append(block)
    if opts["full_analysis"]:
        for analysis in a:
            if analysis["type"] == "topics":
                if len(analysis["body"]) == 0:
                    continue

                topics = ""
                for topic in analysis["body"]:
                    if float(topic["confidence"]) > 0.2:
                        topics += f"*{topic['topic']}* "
                        logger.debug(f"Adding new topic {topic['topic']}")

                # No topics, no block
                if len(topics) == 0:
                    continue

                # Add the block
                block = copy.deepcopy(keywords_block)
                block["text"]["text"] = f"{topics}"
                blocks.append(block)

    # Send this to slack

    client = WebClient(token=opts["slack_token"])
    # Send the blocks to slack
    for channel in opts["slack-channels"]:
        response = client.chat_postMessage(
            channel=channel, blocks=blocks, text="Inbound Call"
        )
        logger.info(f"Posted to {channel} with response {response} for {vCon.uuid}")

    dialogs = vCon.dialog
    for dialog in dialogs:
        response = client.files_remote_add(
            external_id=dialog["url"],
            external_url=dialog["url"],
            title=dialog["url"],
            channels=opts["slack-channels"],
        )
        response = client.files_remote_share(
            external_id=dialog["url"], channels=opts["slack-channels"]
        )

    return vcon_uuid


async def start(opts=default_options):
    logger.info("Starting the slack plugin")
    try:
        # Don't create redis clients in global context as they get started on async
        # event loop which may go away.
        r = server.redis_mgr.get_client()
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts["ingress-topics"])

        while True:
            try:
                message = await p.get_message()
                if message:
                    vConUuid = message["data"].decode("utf-8")
                    logger.info("slack plugin: received vCon: {}".format(vConUuid))
                    await run(vConUuid, opts)
                    for topic in opts["egress-topics"]:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("slack plugin: error: {}".format(e))
    except asyncio.CancelledError:
        logger.debug("slack Cancelled")

    logger.info("slack stopped")

