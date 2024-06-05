from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
import logging
from elasticsearch import Elasticsearch
import json


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

        tenant_attachment = vcon.find_attachment_by_type("tenant")
        tenant_id = None
        if tenant_attachment:
            tenant = json.loads(tenant_attachment["body"])
            tenant_id = tenant["id"]

        # es.index(
        #     index=opts["index"],
        #     id=vcon_dict["uuid"],
        #     document=vcon_dict,
        # )

        # Index the parties, separated by 'role' - id=f"{vcon_uuid}_{party_index}"
        for ind, party in enumerate(vcon_dict["parties"]):
            role = party.get("meta", {}).get("role")
            index_name = "vcon_parties"
            if role:
                index_name += f"_{role}"
            if tenant_id:
                party["tenant_id"] = tenant_id
            party["vcon_id"] = vcon_dict["uuid"]
            es.index(
                index=index_name,
                id=f"{vcon_dict['uuid']}_{ind}",
                document=party,
            )

        # Index the attachments, separated by 'type' - id=f"{vcon_uuid}_{attachment_index}"
        for ind, attachment in enumerate(vcon_dict["attachments"]):
            type = attachment.get("type")  # TODO this might be "purpose" in some of the attachments!!
            index_name = f"vcon_attachments_{type}"
            if attachment["encoding"] == "json":  # TODO may be we need handle different encodings
                attachment["body"] = json.loads(attachment["body"])
            if tenant_id:
                attachment["tenant_id"] = tenant_id
            attachment["vcon_id"] = vcon_dict["uuid"]
            es.index(
                index=index_name,
                id=f"{vcon_dict['uuid']}_{ind}",
                document=attachment,
            )

        # Index the analysis, separated by 'type' - id=f"{vcon_uuid}_{analysis_index}"
        for ind, analysis in enumerate(vcon_dict["analysis"]):
            type = analysis.get("type")
            index_name = f"vcon_analysis_{type}"
            if analysis["encoding"] == "json":  # TODO may be we need handle different encodings
                if isinstance(analysis["body"], str):
                    analysis["body"] = json.loads(analysis["body"])
            if tenant_id:
                analysis["tenant_id"] = tenant_id
            analysis["vcon_id"] = vcon_dict["uuid"]
            es.index(
                index=index_name,
                id=f"{vcon_dict['uuid']}_{ind}",
                document=analysis,
            )

        # Index the dialog - id=f"{vcon_uuid}_{dialog_index}"
        # TODO: Consider separate indexes for different dialog 'types'
        for ind, dialog in enumerate(vcon_dict["dialog"]):
            if tenant_id:
                dialog["tenant_id"] = tenant_id
            dialog["vcon_id"] = vcon_dict["uuid"]
            es.index(
                index="vcon_dialog",
                id=f"{vcon_dict['uuid']}_{ind}",
                document=dialog,
            )

        logger.info("Finished the Elasticsearch storage for vCon: %s", vcon_uuid)
    except Exception as e:
        logger.error(
            f"Elasticsearch storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ", exc_info=True
        )