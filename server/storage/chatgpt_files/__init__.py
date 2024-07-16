from lib.logging_utils import init_logger
from lib.vcon_redis import VconRedis
import json
from openai import OpenAI
import os
import redis_mgr
logger = init_logger(__name__)


default_options = {"purpose": "assistants"}


def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the chatgpt storage for vCon: %s", vcon_uuid)
    client = OpenAI(
        organization=opts["organization_key"],
        project=opts["project_key"],
        api_key=opts["api_key"]
    )
    try:
        vcon = redis_mgr.get_key(vcon_uuid)
        # Upload the vCons
        # Save the vCon as a file
        file_name = f'{vcon_uuid}.vcon.json'
        with open(file_name, "w") as f:
            f.write(json.dumps(vcon))
              
        # Upload the file to OpenAI
        file = client.files.create(file=open(file_name, "rb"), purpose=opts["purpose"])      
        # Remove the file
        os.remove(file_name)  
        client.beta.vector_stores.files.create(
            vector_store_id=opts["vector_store_id"],
            file_id=file.id
        )
        logger.info(f"Finished chatgpt storage for vCon: {vcon_uuid}")
    except Exception as e:
        logger.error(
            f"chatgpt storage plugin: failed to insert vCon: {vcon_uuid}, error: {e}"
        )
        raise e
