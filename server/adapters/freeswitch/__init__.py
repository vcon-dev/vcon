from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
import json
import requests
import os
from urllib.parse import urlsplit, urlunsplit
import vcon
from signalwire.rest import Client as signalwire_client
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
import os
import redis_mgr

logger = init_logger(__name__)

default_options = {
    "SIGNALWIRE_SPACE_URL": "https://xxx.signalwire.com",
    "SIGNALWIRE_PROJECT": "xxxxx-a3a9-489e-914f-yyyyyyyyyy",
    "SIGNALWIRE_TOKEN": "PTb111111111111111111111111111111",
    "egress-lists": ["test-list"]
}

async def run(
    opts=default_options,
):
    logger.debug("Starting freeswitch adapter")
    # Cannot create redis client in global context as it will wait on async
    # event loop which may go away.
    space_url = opts["SIGNALWIRE_SPACE_URL"]
    api_token = opts["SIGNALWIRE_TOKEN"]
    project_id = opts["SIGNALWIRE_PROJECT"]
    auth = (project_id, api_token)

    vcon_redis = VconRedis()
    r = redis_mgr.get_client()
    logger.info("Checking to see if there's new FS recordings") 
    client = signalwire_client(project_id, 
                               api_token,
                               signalwire_space_url = space_url)

    recordings = client.recordings.list()
    for recording in recordings:
        r = client.recordings(recording.sid).fetch()
        call_sid = r.call_sid

        # Fetch the call
        call = client.calls(call_sid).fetch()

        # Construct empty vCon
        vCon = vcon.Vcon()

        # Add some basic call META data
        caller = call.from_formatted
        called = call.to_formatted
        caller_index = vCon.set_party_parameter("tel", caller)
        called_index = vCon.set_party_parameter("tel", called)
        vCon.set_uuid("vcon.dev")

        # Construct the API URL to fetch the recording
        api_url = f"{space_url}{r.uri}"
        parsed_uri = urlsplit(api_url)
        path_without_suffix = os.path.splitext(parsed_uri.path)[0]
        new_parsed_uri = parsed_uri._replace(path=path_without_suffix)
        new_uri = urlunsplit(new_parsed_uri)

        # Send a GET request to the API to download the recording
        response = requests.get(new_uri, auth=auth)

        # Check if the request was successful
        if response.status_code == 200:
            recording_bytes = response.content
            recording_name = "recording.wav"
            vCon.add_dialog_inline_recording(
                recording_bytes,
                call.start_time,
                call.duration,
                [caller_index, called_index], # parties recorded
                "audio/x-wav", # MIME type
                recording_name)
            await vcon_redis.store_vcon(vCon)
            vcon_uuid = str(vCon.uuid)
            print(f"Recording downloaded successfully for call {vcon_uuid}")

            # Push this into the named egress lists
            for name in opts['egress-lists']:
                r.lpush(name, vcon_uuid)
                
        else:
            print(f"Error downloading recording: {response.status_code} - {response.text}")
