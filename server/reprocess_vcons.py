import redis
import os
import json
from datetime import datetime, timedelta


THRESHOLD_START_DAYS = 5  # Will be deleted if it's older than that
THRESHOLD_END_DAYS = 1
REPROCESSED_VCONS_LIMIT = 1

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def is_older_than_threshold(datetime_str):
    # Convert the string to a datetime object
    datetime_obj = datetime.fromisoformat(datetime_str)

    # Get the current datetime
    now = datetime.now(datetime_obj.tzinfo)

    # print(now, datetime_obj, now - datetime_obj)
    return timedelta(days=THRESHOLD_START_DAYS) < now - datetime_obj


def is_newer_than_threshold(datetime_str):
    # Convert the string to a datetime object
    datetime_obj = datetime.fromisoformat(datetime_str)

    # Get the current datetime
    now = datetime.now(datetime_obj.tzinfo)

    return now - datetime_obj > timedelta(days=THRESHOLD_END_DAYS)


def get_ingress_list_name(vcon_data):
    source = None
    for attachement in vcon_data.get("attachments", []):
        if attachement.get("type") == "ingress_info":
            body_data = json.loads(attachement.get("body"))
            source = body_data.get("source")
            break

    # Based on the source - find default ingress list for it
    if source == "volie":
        return "volie_ingress"

    return "default_ingress"


def process_vcon(vcon_key):
    vcon_data = r.json().get(vcon_key)

    if is_older_than_threshold(vcon_data["created_at"]):
        print(vcon_key, "is too old", vcon_data["created_at"])
        # r.delete(vcon_key)
        return

    if not is_newer_than_threshold(vcon_data["created_at"]):
        # print(vcon_data['created_at'], 'is too new')
        return

    ingress_list = get_ingress_list_name(vcon_data)

    print("Pushing", vcon_key, "to", ingress_list)
    # Push only vcon id without prefix
    r.lpush(ingress_list, vcon_key.split(":")[1])
    return True


def process_keys_without_ttl_using_scans():
    cursor = 0
    pattern = "vcon:*"
    reprocessed_vcons = 0

    while True:
        cursor, keys = r.scan(
            cursor=cursor, match=pattern, count=100
        )  # Adjust count as needed
        for key in keys:
            ttl = r.ttl(key)
            if ttl == -1:
                # TTL is not set - we might need to reprocess them
                if process_vcon(key):
                    reprocessed_vcons += 1
                    if (
                        REPROCESSED_VCONS_LIMIT
                        and reprocessed_vcons >= REPROCESSED_VCONS_LIMIT
                    ):
                        print("Repocessed enough vcons, exiting")
                        return

        # Break the loop when cursor returns to '0', indicating the scan is complete
        if cursor == 0:
            break


if __name__ == "__main__":
    process_keys_without_ttl_using_scans()
