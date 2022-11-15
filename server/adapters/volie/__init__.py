import asyncio
from pydoc import doc
import async_timeout
import redis.asyncio as redis
import json
import vcon
import urllib
import datetime
import logging 

logger = logging.getLogger(__name__)


def adapter_meta(body, type):
    meta= {}
    meta['src'] = 'conserver'
    meta['adapter'] = "volie"
    meta['received_at'] = datetime.datetime.now().isoformat()
    meta['payload'] = body
    meta['type'] = type
    return meta

def create_vcon_from_email(body):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        type = body.get('kind', 'unknown')
        vCon.attachments.append(adapter_meta(body, type))
        vCon.set_party_parameter("mailto", body['email_to_address'], -1)
        vCon.set_party_parameter("name", body['customer_full_name'], 0)
        vCon.set_party_parameter("mailto", body['email_from_address'], -1)
        vCon.add_dialog_inline_text(json.dumps(body), body['email_sent_at'],0, 0, body['email_mime_type'])
        return vCon

    except Exception as e:
        print(e)
        return None


def create_vcon_from_sms(body):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        type = body.get('kind', 'unknown')
        vCon.attachments.append(adapter_meta(body, type))

        caller = body.get(body['message_from'], 'unknown')
        called = body.get(body['message_to'], 'unknown')
        vCon.set_party_parameter("tel", caller)
        vCon.set_party_parameter("tel", called)
        vCon.add_dialog_inline_text(body['message_body'], body['message_sent_at'],0, 0, "MIMETYPE_TEXT_PLAIN")
        return vCon

    except Exception as e:
        print(e)
        return None

def create_vcon_from_phone_call(body):
    try:
        # Construct empty vCon, set meta data
        vCon = vcon.Vcon()
        type = body.get('kind', 'unknown')
        vCon.attachments.append(adapter_meta(body, type))

        caller = body.get('from_number', 'unknown')
        called = body.get('to_number', 'unknown')
        vCon.set_party_parameter("tel", caller,-1)
        vCon.set_party_parameter("tel", called, -1)

        # Recording
        recording_url = body.get('recording', None)
        if recording_url:
            # Remove query string
            host = recording_url.split("?")[0]
            # The file name is the last part of the URL
            recording_filename = host.split("/")[-1]

            # Download the recording
            try:
                # Download the recording
                recording_bytes = urllib.request.urlopen(recording_url).read()
                starttime = body.get('call_date', None)
                duration = body.get('call_duration', None)


                vCon.add_dialog_inline_recording(
                recording_bytes,
                starttime,
                duration,
                [0, 1], # parties recorded
                "audio/x-wav", # MIME type
                recording_filename)

            except urllib.error.HTTPError as err:
                error_msg = "Error retrieving recording from " + recording_url
                error_type = "HTTPError"
                error_time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                vCon.attachments.append({"error_msg": error_msg, "error_type": error_type, "error_time": error_time})
        return vCon

    except Exception as e:
        logger.debug("create_vcon_from_phone_call error: {}".format(e))
        return None

default_options = {
    "name": "volie",
    "ingress-list": ["volie-conserver-feed"],
    "egress-topics":["ingress-vcons"],
}

async def start(opts=default_options):
    logger.info("Starting the volie adapter")
    # Setup redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        try:
            async with async_timeout.timeout(10):
                for ingress_list in opts["ingress-list"]:
                    list, data = await r.blpop(ingress_list)
                    if data is None:
                        continue
                    try:
                        payload = json.loads(data)
                        message = json.loads(payload.get("Message"))
                        body = json.loads(message['default']['body'])

                        # Construct empty vCon, set meta data
                        vCon = vcon.Vcon()

                        # Decode it
                        kind = body.get('kind', 'unknown')
                        if kind == 'NEW_MESSAGE':
                            vCon = create_vcon_from_sms(body)
                        elif kind == 'NEW_CALL':
                            vCon = create_vcon_from_phone_call(body)
                        elif kind == 'NEW_EMAIL':
                            vCon = create_vcon_from_email(body)
                        else:
                            logger.debug("What the heck is this? {}".format(body))
                            continue
                        logger.info("Incoming Volie vCon: {}".format(vCon.uuid))
                        cleanvCon = json.loads(vCon.dumps())
                        await r.json().set("vcon:{}".format(vCon.uuid), cleanvCon)
                        await r.publish("ingress-vcons", str(vCon.uuid))
                    except Exception as e:
                        logger.debug("volie adapter error: {}".format(e))

        except asyncio.TimeoutError:
            pass    
        except asyncio.CancelledError:
            logger.info("Volie Cancelled")
            break

    logger.info("Volie Adapter stopped")    

