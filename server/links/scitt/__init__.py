import os
from lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
from links.scitt import create_signed_statement
import hashlib
import json
import requests


logger = init_logger(__name__)

default_options = {
    "client_id": None,
    "client_secret": None,
    "signing_key_path": None,
    "message": None,
    "issuer": "ANONYMOUS CONSERVER",
}


def run(
    vcon_uuid,
    link_name,
    opts=default_options,
):
    module_name = __name__.split(".")[-1]
    logger.info(f"Starting {module_name}: {link_name} plugin for: {vcon_uuid}")
    merged_opts = default_options.copy()
    merged_opts.update(opts)
    opts = merged_opts

    vcon_redis = VconRedis()
    vCon = vcon_redis.get_vcon(vcon_uuid)

    # Generate sha256 for vcon json
    vcon_json = vCon.to_json()
    vcon_hash = hashlib.sha256(vcon_json.encode()).hexdigest()

    payload = {
        "message": opts["message"],
        "hash": vcon_hash,
    }

    payload_s = json.dumps(payload)

    signing_key_path = os.path.join(opts["signing_key_path"])
    signing_key = create_signed_statement.open_signing_key(signing_key_path)
    signed_statement = create_signed_statement.create_signed_statement(
        signing_key,
        payload_s,
        subject=vcon_uuid,
        issuer=opts["issuer"],
        content_type="application/json",
    )

    # Get the token using the requests library
    token_response = requests.post(
        "https://app.datatrails.ai/archivist/iam/v1/appidp/token",
        data={
            "grant_type": "client_credentials",
            "client_id": opts["client_id"],
            "client_secret": opts["client_secret"],
        },
    )
    token = token_response.json()["access_token"]

    headers = {"Content-Type": "text/plain", "Authorization": f"Bearer {token}"}

    response = requests.request(
        "POST",
        "https://app.datatrails.ai/archivist/v1/publicscitt/entries",
        headers=headers,
        data=signed_statement,
    )

    print("Response:", response.text)

    return vcon_uuid
