import asyncio
import async_timeout
import redis.asyncio as redis
import json
from lib.logging_utils import init_logger
import vcon
import datetime
from settings import REDIS_URL
from redis.commands.json.path import Path


logger = init_logger(__name__)

logger.info("Starting the quiq adapter")

default_options = {
    "name": "quiq",
    "ingress-list": ["quiq-conserver-feed"],
    "egress-topics": ["ingress-vcons"],
}


async def start(opts=default_options):
    logger.info("Starting the quiq adapter")

    # Setup redis
    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    while True:
        try:
            async with async_timeout.timeout(10):
                for ingress_list in opts["ingress-list"]:
                    data = await r.lpop(ingress_list)
                    if data is None:
                        continue
                    try:
                        payload = json.loads(data)
                        body = payload.get("default")

                        # Construct empty vCon, set meta data
                        vCon = vcon.Vcon()
                        vCon.set_party_parameter("tel", body["src"], -1)
                        vCon.set_party_parameter("tel", body["dst"], -1)

                        # Copy over the transcript from the message
                        messages = body["event_payload"]["messages"]
                        transcript = ""
                        start_time = None
                        for message in messages:
                            if start_time is None:
                                timestamp = int(message["timestamp"])
                                start_time = timestamp / 1000

                            line = "{}: {}\n".format(message["author"], message["text"])
                            transcript += line

                        vCon.add_dialog_inline_text(
                            transcript, start_time, 0, 10000, "MIMETYPE_TEXT_PLAIN"
                        )
                        # Set the adapter meta so we know where this thing came from
                        adapter_meta = {
                            "adapter": "quiq",
                            "adapter_version": "0.1.0",
                            "src": ingress_list,
                            "type": "chat_completed",
                            "received_at": datetime.datetime.now().isoformat(),
                            "payload": body,
                        }
                        vCon.attachments.append(adapter_meta)

                        # Publish the vCon
                        logger.debug("New vCon created: {}".format(vCon.uuid))
                        key = "vcon:{}".format(vCon.uuid)
                        cleanVcon = json.loads(vCon.dumps())
                        await r.json().set(key, Path.root_path(), cleanVcon)
                        for egress_topic in opts["egress-topics"]:
                            await r.publish(egress_topic, vCon.uuid)
                    except Exception as e:
                        logger.error("Quiq adapter error: {}".format(e))

        except asyncio.TimeoutError:
            logger.info("quiq async timeout")
            pass

        except asyncio.CancelledError:
            logger.info("quiq Cancelled")
            break

        except Exception as e:
            logger.debug("quiq adapter error: {}".format(e))

    logger.info("Quiq adapter stopped")
