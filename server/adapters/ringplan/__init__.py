from datetime import date
from datetime import datetime
from urllib.parse import urlparse
from urllib.parse import urlparse, parse_qs
import async_timeout
import asyncio
import humanize
import json
import logging
import redis.asyncio as redis
from redis.commands.json.path import Path
import urllib
import vcon
from settings import REDIS_URL, LOG_LEVEL, ENV, HOSTNAME
import jose

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.info('RingPlan adapter loading')
logger.debug("Debuggingly")

default_options = {
    "name": "ringplan",
    "ingress-list": [f"ringplan-conserver-feed-{ENV}", "ringplan-conserver-feed"],
    "egress-topics":["ingress-vcons"],
}

async def start(opts=default_options):
    logger.info("Starting the ringplan adapter")
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
                        original_msg = json.loads(payload.get("Message"))
                        payload = original_msg.get("payload")

                        # Construct empty vCon, set meta data
                        vCon = vcon.Vcon()

                        # Download the recording and attach it to the vCon
                        recording_url = payload.get("recording").get("url")
                        # Remove query string
                        host = recording_url.split("?")[0]
                        # The file name is the last part of the URL
                        recording_filename = host.split("/")[-1]

                        # Download the recording
                        parse_result = urlparse(recording_url)
                        dict_result = parse_qs(parse_result.query)
                        expires = datetime.fromtimestamp(int(dict_result.get("Expires")[0]))
                        expires_human = humanize.precisedelta(expires)

                        if (datetime.today() > expires):
                            logger.debug("Recording expired {} ago.".format(expires_human))

                        else:   
                            try:
                                # Download the recording
                                starttime = payload.get("cdr").get("starttime")
                                duration = payload.get("cdr").get("duration")
                                recording_bytes = urllib.request.urlopen(recording_url).read()

                                # Store this in local file system
                                local_filename = f"static/{str(vCon.uuid)}_{0}.wav"
                                f=open(local_filename, "wb")
                                f.write(recording_bytes)
                                f.close()
                                external_url = f"{HOSTNAME}/static/{str(vCon.uuid)}_{0}.wav"
                                vCon.add_dialog_external_recording(
                                    recording_bytes,
                                    starttime,
                                    duration,
                                    [0, 1], # parties recorded
                                    external_url,
                                    file_name=recording_filename
                                )
                                logger.debug("Recording successfully downloaded and attached to vCon")
                            except urllib.error.HTTPError as err:
                                error_msg = "Error retrieving recording from " + recording_url
                                error_type = "HTTPError"
                                error_time = date.today().strftime("%m/%d/%Y, %H:%M:%S")
                                vCon.attachments.append({"error_msg": error_msg, "error_type": error_type, "error_time": error_time})
                                logger.debug(f"Recording not downloaded: {error_msg}, {error_type}, {error_time}")
        
                        if payload.get("cdr").get("direction") == "IN":
                            caller = payload.get("cdr").get("src")
                            called = payload.get("cdr").get("dst")
                            agent_party = 1
                        else:
                            caller = payload.get("cdr").get("dst")
                            called = payload.get("cdr").get("src")

                        vCon.set_party_parameter("tel", caller, -1)
                        vCon.set_party_parameter("tel", called, -1)

                        # Set the adapter meta so we know where the this came from
                        adapter_meta= {
                            "adapter": "ringplan",
                            "adapter_version": "0.1.0",
                            "src": ingress_list,
                            "type": "call_completed",
                            "received_at": datetime.now().isoformat(),
                            "payload": original_msg
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
                        logger.error("RingPlan adapter error: {}".format(e))

        except asyncio.CancelledError:
            logger.info("ringplan Cancelled")
            break
        except asyncio.TimeoutError:
            logger.info("ringplan async timeout")
            pass    


    logger.info("RingPlan adapter stopped")
    if logger.isEnabledFor(logging.DEBUG):
      async_tasks = asyncio.all_tasks()
      logger.debug("{} tasks".format(len(async_tasks)))



