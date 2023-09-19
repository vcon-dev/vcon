import os
import time
import wave
import uuid
import boto3
from pyVoIP.VoIP import VoIPPhone, InvalidStateError
from fastapi import BackgroundTasks
from botocore.exceptions import ClientError
from lib.logging_utils import init_logger
import vcon
import redis_mgr
import traceback
from datetime import datetime
from api import add_vcon_to_set

logger = init_logger(__name__)
_config = None

def __init__(config):
    logger.info(f"Starting SIP_REC with {config}")
    _config = config

    phone=VoIPPhone(
        _config["SIP_SERVER_IP"],
        _config["SIP_SERVER_PORT"],
        _config["SIP_SERVER_PASS"],
        callCallback=answer,
        myIP=_config["SIP_MY_IP"],
        sipPort=_config["SIP_PORT"],
        rtpPortLow=_config["SIP_RTP_PORT_LOW"],
        rtpPortHigh=_config["SIP_RTP_PORT_HIGH"])

    phone.start()


def answer(call): # This will be your callback function for when you receive a phone call.
    logger.debug(f"Answering call {call}")
    try:
        call.answer()

        # We want to record the call. Use the read_audio function to get the audio data, which is blocking. 
        # Put that in a separate thread so we can do other things while we wait for the audio data, and
        # save it to a file.
        background_tasks = BackgroundTasks()

        # Schedule the read_audio function to run every second
        background_tasks.add_task(record_audio, call)

        # Start the background tasks
        background_tasks.start()
    except InvalidStateError:
        pass
    except:
        call.hangup()
            
def record_audio(call):
    # This is a new call. Get an ID for it.
    call_id = uuid.uuid4()
    file_name = f"{_config['PATH_NAME']}audio-{call_id}.wav"
    logger.debug(f"Recording audio for call {call_id} to {file_name}")
    
    READ_LEN = 160
    BLANK = b'\x00' * READ_LEN
    POLL_INTERVAL = 0.1 

    # Read the audio data from the call
    
    # Start a loop with a sleep so we don't hog the CPU
    with wave.open(file_name, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        in_call = True
        while in_call:
            # Read the audio data from the call
            audio_data = call.read_audio()
            if audio_data != BLANK:
                wav_file.writeframes(audio_data)
            # Check if the call is still active
            if call.state == "ENDED":
                logger.debug(f"Call {call_id} is no longer active. Cleaning up.")
                in_call = False
            time.sleep(POLL_INTERVAL)

    logger.debug(f"Finished recording audio for call {call_id}.")
    # Upload the file to S3
    if _config["S3_BUCKET"] and _config["S3_KEY"]:
        upload_to_s3(file_name)
        logger.debug(f"Uploaded file {file_name} to S3.")
        # Delete the file
        os.remove(file_name)
        logger.debug(f"Deleted file {file_name}.")
    else:
        logger.debug(f"Not uploading file {file_name} to S3.")

    generated_vcon = create_vcon(call, call_id, file_name)

    # Save the vCon to redis
    save_vcon_to_redis(generated_vcon, call_id)
    logger.debug(f"Generated vCon {generated_vcon} for call {call_id}.")

    # Put this into the ingress list
    if _config["INGRESS_LIST"]:
        push_vcon_to_list(call_id, _config["INGRESS_LIST"])
        logger.debug(f"Pushed call {call_id} to ingress list {_config['INGRESS_LIST']}.")

    logger.debug(f"Finished processing call {call_id}.")
    return True


# This function loads the wave file to S3
def upload_to_s3(file_name):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, _config["S3_BUCKET"], _config["S3_KEY"] )
        logger.debug(f"Uploaded file {file_name} to S3.")
        logger.debug(response)
    except ClientError as e:
        logger.error(e)
        return False
    return True


def create_vcon(call, call_id, wav_file_name):

    # Construct empty vCon
    vCon = vcon.Vcon()

    # Add some basic call META data
    caller = "+18881234567"
    called = "1234"
    vCon.set_party_tel_url(caller)
    vCon.set_party_tel_url(called)

    # Add a recording of the call
    recording_name = wav_file_name

    with open(recording_name, 'rb') as file_handle:
        recording_bytes = file_handle.read()
    vCon.add_dialog_inline_recording(
        recording_bytes,
        "Mon, 23 May 2022 20:09:01 -0000",
        23.5, # sec. duration
        [0, 1], # parties recorded
        "audio/x-wav", # MIME type
        recording_name)

    # Serialize the vCon to a JSON format string
    json_string = vCon.dumps()
    print(json_string)

def save_vcon_to_redis(vcon, call_id):
    try:
        r = redis_mgr.get_client()
        key = f"vcon:{str(call_id)}"
        created_at = datetime.fromisoformat(vcon["created_at"])
        timestamp = int(created_at.timestamp())

        # Store the vcon in redis
        logger.debug(
            "Posting vcon  {} len {}".format(call_id, len(vcon))
        )
        r.json().set(key, "$", vcon)

        # Add the vcon to the sorted set
        logger.debug("Adding vcon {} to sorted set".format(call_id))
        add_vcon_to_set(key, timestamp)

    except Exception:
        # Print all of the details of the exception
        logger.info(traceback.format_exc())
        return None

def push_vcon_to_list(call_id: str, ingress_list: str):
    try:
        r = redis_mgr.get_client()
        r.lpush(ingress_list, call_id)
    except Exception as e:
        logger.info("Error: {}".format(e)) 
        