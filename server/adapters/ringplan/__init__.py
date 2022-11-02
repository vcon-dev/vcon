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
import urllib
import vcon

logger = logging.getLogger(__name__)

async def start():
    logger.info("Starting the ringplan adapter")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(10):
                list, data = await r.blpop("ringplan-conserver-feed")
                if data is None:
                    continue

                try:
                    list = list.decode()
                    payload = json.loads(data.decode())
                    original_msg = json.loads(payload.get("Message"))

                    # Construct empty vCon, set meta data
                    vCon = vcon.Vcon()
                    payload = original_msg.get("payload")

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
                            recording_bytes = urllib.request.urlopen(recording_url).read()
                            starttime = payload.get("cdr").get("starttime")
                            duration = payload.get("cdr").get("duration")

                            vCon.add_dialog_inline_recording(
                            recording_bytes,
                            starttime,
                            duration,
                            [0, 1], # parties recorded
                            "audio/ogg", # MIME type
                            recording_filename)
                            logger.debug("Recording successfully downloaded and attached to vCon")

                        except urllib.error.HTTPError as err:
                            error_msg = "Error retrieving recording from " + recording_url
                            error_type = "HTTPError"
                            error_time = date.today().strftime("%m/%d/%Y, %H:%M:%S")
                            vCon.attachments.append({"error_msg": error_msg, "error_type": error_type, "error_time": error_time})
                            logger.debug("Recording not downloaded, expired")


                    if payload.get("cdr").get("direction") == "IN":
                        caller = payload.get("cdr").get("src")
                        called = payload.get("cdr").get("dst")
                        vCon.set_party_parameter("tel", caller)
                        vCon.set_party_parameter("tel", called)
                        agent_party = 1
                    else:
                        caller = payload.get("cdr").get("dst")
                        called = payload.get("cdr").get("src")
                        vCon.set_party_parameter("tel", caller)
                        vCon.set_party_parameter("tel", called)
                        agent_party = 0
                    
                    vCon.parties[agent_party]["network"] = payload.get("cdr").get("network")
                    vCon.parties[agent_party]["direction"] =  payload.get("cdr").get("direction")
                    vCon.parties[agent_party]["orgalias"] =  payload.get("cdr").get("orgalias")
                    vCon.parties[agent_party]["pbx_cnum"] =  payload.get("cdr").get("pbx_cnum")
                    vCon.parties[agent_party]["pbx_dcontext"] =  payload.get("cdr").get("pbx_dcontext")
                    vCon.parties[agent_party]["pbx_dst"] =  payload.get("cdr").get("pbx_dst")
                    vCon.parties[agent_party]["releasecausecode"] =  payload.get("cdr").get("releasecausecode")
                    vCon.parties[agent_party]["status"] =  payload.get("cdr").get("status")

                    # Set the adapter meta so we know where the this came from
                    adapter_meta= {}
                    adapter_meta['src'] = 'conserver'
                    adapter_meta['type'] = 'call_completed'
                    adapter_meta['adapter'] = "ringplan"
                    adapter_meta['received_at'] = datetime.datetime.now().isoformat()
                    adapter_meta['payload'] = original_msg
                    vCon.attachments.append(adapter_meta)

                    # Publish the vCon
                    logger.info("New vCon created: {}".format(vCon.uuid))
                    await r.set("vcon-{}".format(vCon.uuid), vCon.dumps())
                    await r.publish("ingress-vcons",  str(vCon.uuid))
                except Exception as e:
                    logger.debug("Error in ringplan adapter: {}".format(e))
                    break

        except asyncio.CancelledError:
            logger.debug("ringplan Cancelled")
            break
        except asyncio.TimeoutError:
            pass    


    logger.info("Quiq adapter stopped")    



