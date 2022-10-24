import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import urllib
import datetime
from pydub import AudioSegment
from urllib.parse import urlparse
import sys

sys.path.append("../..")
import vcon

async def start():
    print("Starting the ringplan adapter")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(5):
                list, data = await r.blpop("ringplan-conserver-feed")
                if data is None:
                    await asyncio.sleep(1)
                    continue

                print("Found a ring_plan")
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

                    try:
                        # Download the recording
                        print("Downloading recording from: ", recording_url)
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
                        print("Recording downloaded")

                    except urllib.error.HTTPError as err:
                        error_msg = "Error retrieving recording from " + recording_url
                        error_type = "HTTPError"
                        error_time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                        vCon.attachments.append({"error_msg": error_msg, "error_type": error_type, "error_time": error_time})
                        print("Recording not downloaded, expired")




                    if payload.get("cdr").get("direction") == "IN":
                        caller = payload.get("cdr").get("src")
                        called = payload.get("cdr").get("dst")
                        vCon.set_party_tel_url(caller,-1)
                        vCon.set_party_tel_url(called,-1)
                        agent_party = 1
                    else:
                        caller = payload.get("cdr").get("dst")
                        called = payload.get("cdr").get("src")
                        vCon.set_party_tel_url(caller,-1)
                        vCon.set_party_tel_url(called,-1)
                        agent_party = 0
                    
                    vCon.parties[agent_party]["network"] = payload.get("cdr").get("network")
                    vCon.parties[agent_party]["direction"] =  payload.get("cdr").get("direction")
                    vCon.parties[agent_party]["orgalias"] =  payload.get("cdr").get("orgalias")
                    vCon.parties[agent_party]["pbx_cnum"] =  payload.get("cdr").get("pbx_cnum")
                    vCon.parties[agent_party]["pbx_dcontext"] =  payload.get("cdr").get("pbx_dcontext")
                    vCon.parties[agent_party]["pbx_dst"] =  payload.get("cdr").get("pbx_dst")
                    vCon.parties[agent_party]["releasecausecode"] =  payload.get("cdr").get("releasecausecode")
                    vCon.parties[agent_party]["status"] =  payload.get("cdr").get("status")

        
                    adapter_meta= {}
                    adapter_meta['src'] = 'conserver'
                    adapter_meta['type'] = 'call_completed'
                    adapter_meta['adapter'] = "ringplan"
                    adapter_meta['received_at'] = datetime.datetime.now().isoformat()
                    adapter_meta['payload'] = original_msg

                    vCon.attachments.append(adapter_meta)

                    print("Sending vCon to server")
                    print(vCon)
                    await r.publish("ingress-events",  vCon.dumps())
                except Exception as e:
                    print("Error in ringplan adapter: {}".format(e))
                    break

        except asyncio.CancelledError:
            print("ringplan Cancelled")
            break
        except asyncio.TimeoutError:
            print("ringplan Timeout")
            pass    


    print("Adapter stopped")    



