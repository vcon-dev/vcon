from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
import logging
from elasticsearch import Elasticsearch


logger = init_logger(__name__)
# Disable Elastic Search API requests logs
logging.getLogger("elastic_transport.transport").setLevel(logging.WARNING)

default_options = {
    "name": "elasticsearch",
    "cloud_id": "",
    "api_key": "",
    "index": "vcon_index",
}


def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the Elasticsearch storage for vCon: %s", vcon_uuid)
    try:
        es = Elasticsearch(
            cloud_id=opts["cloud_id"],
            api_key=opts["api_key"],
        )
        vcon_redis = VconRedis()
        vcon = vcon_redis.get_vcon(vcon_uuid)
        vcon_dict = vcon.to_dict()
        es.index(
            index=opts["index"],
            id=vcon_dict["uuid"],
            document=vcon_dict,
        )
        logger.info("Finished the Elasticsearch storage for vCon: %s", vcon_uuid)
    except Exception as e:
        logger.error(
            f"Elasticsearch storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} "
        )