import pymongo
import redis.asyncio as redis
import json
from lib.logging_utils import init_logger
from settings import MONGODB_URL
from datetime import datetime
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
vcon_redis = VconRedis()
logger = init_logger(__name__)


default_options = {"name": "mongo", "database":"conserver", "collection_name":"vcons"}

def prepare_vcon_for_mongo(vcon: dict) -> dict:
    clean_vcon = json.loads(vcon.dumps())
    clean_vcon['_id'] = vcon.uuid
    clean_vcon['created_at'] = datetime.fromisoformat(clean_vcon['created_at'])
    for dialog in clean_vcon['dialog']:
        dialog['start'] = datetime.fromisoformat(dialog['start'])
    return clean_vcon


async def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the mongo storage")
    client = pymongo.MongoClient(MONGODB_URL)
    try:
        vcon = await vcon_redis.get_vcon(vcon_uuid)
        db = client[opts['database']]
        collection = db[opts['collection']]
        results = collection.insert_one(
            prepare_vcon_for_mongo(vcon)
        )
        logger.info(f"mongo storage plugin: inserted vCon: {vcon_uuid}, results: {results} ")
    except Exception as e:
        logger.error(f"mongo storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ")
        raise e
    