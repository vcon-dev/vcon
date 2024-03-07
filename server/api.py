import traceback
from datetime import datetime
from typing import Dict, List, Union, Optional
from uuid import UUID

import redis_mgr
from redis_mgr import redis_async
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from lib.logging_utils import init_logger
from load_config import load_config
from peewee import CharField, Model
from playhouse.postgres_ext import (
    BinaryJSONField,
    DateTimeField,
    PostgresqlExtDatabase,
    UUIDField,
)
from pydantic import BaseModel
from dlq_utils import get_ingress_list_dlq_name
from settings import VCON_SORTED_SET_NAME, VCON_STORAGE

logger = init_logger(__name__)
logger.info("Api starting up")


# Load FastAPI app
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Vcon(BaseModel):
    vcon: str
    uuid: UUID
    created_at: Union[int, str, datetime]
    subject: Optional[str] = None
    redacted: dict = {}
    appended: Optional[dict] = None
    group: List[Dict] = []
    parties: List[Dict] = []
    dialog: List[Dict] = []
    analysis: List[Dict] = []
    attachments: List[Dict] = []
    meta: dict = {}


if VCON_STORAGE:

    class VConPeeWee(Model):
        id = UUIDField(primary_key=True)
        vcon = CharField()
        uuid = UUIDField()
        created_at = DateTimeField()
        updated_at = DateTimeField(null=True)
        subject = CharField(null=True)
        vcon_json = BinaryJSONField(null=True)
        type = CharField(null=True)

        class Meta:
            table_name = "vcons"
            database = PostgresqlExtDatabase(VCON_STORAGE)


async def add_vcon_to_set(vcon_uuid: UUID, timestamp: int):
    await redis_async.zadd(VCON_SORTED_SET_NAME, {vcon_uuid: timestamp})


# These are the vCon data models
@app.get(
    "/vcon",
    response_model=List[str],
    summary="Gets a list of vCon UUIDs",
    description=(
        "Enables pagination of vCon UUIDs. "
        "Use the page and size parameters to paginate the results. "
        "Can also filter by date with the since and until parameters."
    ),
    tags=["vcon"],
)
async def get_vcons(
    page: int = 1, size: int = 50, since: datetime = None, until: datetime = None
):
    if VCON_STORAGE:
        offset = (page - 1) * size
        query = VConPeeWee.select()
        if since:
            query = query.where(VConPeeWee.created_at > since)
        if until:
            query = query.where(VConPeeWee.created_at < until)
        query = query.order_by(VConPeeWee.created_at.desc()).offset(offset).limit(size)
        r = [str(vcon.uuid) for vcon in query]
        return r

    else:
        # Redis is storing the vCons. Use the vcons sorted set to get the vCon UUIDs
        r = redis_mgr.get_client()
        until_timestamp = "+inf"
        since_timestamp = "-inf"

        # We can either use the page and offset, or the since and until parameters
        if since:
            since_timestamp = int(since.timestamp())
        if until:
            until_timestamp = int(until.timestamp())
        offset = (page - 1) * size
        vcon_uuids = await redis_async.zrevrangebyscore(
            VCON_SORTED_SET_NAME,
            until_timestamp,
            since_timestamp,
            start=offset,
            num=size,
        )
        logger.info("Returning vcon_uuids: {}".format(vcon_uuids))

        # Convert the vcon_uuids to strings and strip the vcon: prefix
        vcon_uuids = [vcon.split(":")[1] for vcon in vcon_uuids]
        return vcon_uuids


@app.get(
    "/vcon/{vcon_uuid}",
    response_model=Vcon,
    summary="Gets a particular vCon by UUID",
    description="How to get a particular vCon by UUID",
    tags=["vcon"],
)
async def get_vcon(vcon_uuid: UUID):
    if VCON_STORAGE:
        q = VConPeeWee.select().where(VConPeeWee.uuid == vcon_uuid)
        r = q.get()
        # If we didn't find the vcon, return a 404, otherwise return the vcon
        if r is None:
            return JSONResponse(status_code=404)
        else:
            return JSONResponse(content=r.vcon_json)

    # Redis is storing the vCons. Use the vcons sorted set to get the vCon UUIDs
    try:
        r = redis_mgr.get_client()
        vcon = await redis_async.json().get(f"vcon:{str(vcon_uuid)}")
    except Exception:
        logger.info(traceback.format_exc())
        return None
    logger.debug(
        "Returning whole vcon for {} found: {}".format(vcon_uuid, vcon is not None)
    )
    if vcon is None:
        return JSONResponse(content=None, status_code=404)
    else:
        return JSONResponse(content=vcon)


@app.post(
    "/vcon",
    response_model=Vcon,
    summary="Inserts a vCon into the database",
    description="How to insert a vCon into the database.",
    tags=["vcon"],
)
async def post_vcon(inbound_vcon: Vcon):
    if VCON_STORAGE:
        # Create a new vcon in the database
        # Use peewee
        id = inbound_vcon.uuid
        vcon_json = inbound_vcon.model_dump_json()
        uuid = inbound_vcon.uuid
        created_at = inbound_vcon.created_at
        updated_at = inbound_vcon.updated_at or inbound_vcon.created_at
        subject = inbound_vcon.subject
        type = inbound_vcon.type
        VConPeeWee.create(
            id=id,
            uuid=uuid,
            created_at=created_at,
            updated_at=updated_at,
            subject=subject,
            type=type,
            vcon_json=vcon_json,
        )
        return JSONResponse(content=inbound_vcon.dict(), status_code=201)
    else:
        try:
            dict_vcon = inbound_vcon.dict()
            dict_vcon["uuid"] = str(inbound_vcon.uuid)
            key = f"vcon:{str(dict_vcon['uuid'])}"
            created_at = datetime.fromisoformat(dict_vcon["created_at"])
            timestamp = int(created_at.timestamp())

            # Store the vcon in redis
            logger.debug(
                "Posting vcon  {} len {}".format(inbound_vcon.uuid, len(dict_vcon))
            )
            await redis_async.json().set(key, "$", dict_vcon)
            # Add the vcon to the sorted set
            logger.debug("Adding vcon {} to sorted set".format(inbound_vcon.uuid))
            await add_vcon_to_set(key, timestamp)
        except Exception:
            # Print all of the details of the exception
            logger.info(traceback.format_exc())
            return None
        logger.debug("Posted vcon  {} len {}".format(inbound_vcon.uuid, len(dict_vcon)))
        return JSONResponse(content=dict_vcon, status_code=201)


@app.delete(
    "/vcon/{vcon_uuid}",
    status_code=204,
    summary="Deletes a particular vCon by UUID",
    description="How to remove a vCon from the conserver.",
    tags=["vcon"],
)
async def delete_vcon(vcon_uuid: UUID):
    # FIX: support the VCON_STORAGE case
    try:
        await redis_async.json().delete(f"vcon:{str(vcon_uuid)}")
    except Exception:
        # Print all of the details of the exception
        logger.info(traceback.format_exc())
        raise HTTPException(status_code=500)


# Ingress and egress endpoints for vCon IDs
# Create an endpoint to push vcon IDs to one or more redis lists
@app.post(
    "/vcon/ingress",
    status_code=204,
    summary="Inserts a vCon UUID into one or more chains",
    description="Inserts a vCon UUID into one or more chains.",
    tags=["chain"],
)
async def post_vcon_ingress(vcon_uuids: List[str], ingress_list: str):
    try:
        for vcon_id in vcon_uuids:
            await redis_async.rpush(
                ingress_list,
                vcon_id,
            )
    except Exception as e:
        logger.info("Error: {}".format(e))
        raise HTTPException(status_code=500)


# Create an endpoint to pop vcon IDs from one or more redis lists
@app.get(
    "/vcon/egress",
    status_code=204,
    summary="Removes one or more vCon UUIDs from the output of a chain (egress)",
    description="Removes one or more vCon UUIDs from the output of a chain (egress)",
    tags=["chain"],
)
async def get_vcon_egress(egress_list: str, limit=1):
    try:
        vcon_uuids = []
        for i in range(limit):
            vcon_uuid = await redis_async.rpop(egress_list)
            if vcon_uuid:
                vcon_uuids.append(vcon_uuid)
        return JSONResponse(content=vcon_uuids)

    except Exception as e:
        logger.info("Error: {}".format(e))
        raise HTTPException(status_code=500)


# Create an endpoint to count the number of vCon UUIds in a redis list
@app.get(
    "/vcon/count",
    status_code=204,
    summary="Returns the number of vCons at the end of a chain",
    description="Returns the number of vCons at the end of a chain.",
    tags=["chain"],
)
async def get_vcon_count(egress_list: str):
    try:
        count = await redis_async.llen(egress_list)
        return JSONResponse(content=count)

    except Exception as e:
        logger.info("Error: {}".format(e))
        raise HTTPException(status_code=500)


@app.get(
    "/config",
    status_code=200,
    summary="Returns the config file for the conserver",
    description="Returns the config file for the conserver",
    tags=["config"],
)
async def get_config():
    try:
        config = await redis_async.json().get("config")
        return JSONResponse(content=config)

    except Exception as e:
        logger.info("Error: {}".format(e))
        raise HTTPException(status_code=500)


# THis endpoint is used to update the config file, then calls
# the load_config endpoint to load the new config file into redis
@app.post(
    "/config",
    status_code=204,
    summary="Updates the config file for the conserver",
    description="Updates the config file for the conserver",
    tags=["config"],
)
async def post_config(config: Dict, update_file_name=None):
    try:
        load_config(config)
    except Exception as e:
        logger.info("Error: {}".format(e))
        raise HTTPException(status_code=500)


# This endpoint clears the config
@app.delete(
    "/config",
    status_code=204,
    summary="Clears the config file for the conserver",
    description="Clears the config file for the conserver",
    tags=["config"],
)
async def delete_config():
    try:
        await redis_async.delete("config")
        # Delete the links
        links = await redis_async.keys("link:*")
        for link in links:
            await redis_async.delete(link)
        # Delete the storages
        storages = await redis_async.keys("storage:*")
        for storage in storages:
            await redis_async.delete(storage)
        # Delete the chains
        chains = await redis_async.keys("chain:*")
        for chain in chains:
            await redis_async.delete(chain)

    except Exception as e:
        logger.info("Error: {}".format(e))
        raise HTTPException(status_code=500)


# Reprocess Dead Letter Queue
@app.post(
    "/dql/reprocess",
    status_code=200,
    summary="Reprocess the dead letter queue",
    description="Move the dead letter queue vcons back to the ingress chain",
    tags=["chain"],
)
async def post_dlq_reprocess(ingress_list: str):
    # Get all items from redis list and move them back to the ingress list
    dlq_name = get_ingress_list_dlq_name(ingress_list)
    counter = 0
    while item := await redis_async.rpop(dlq_name):
        await redis_async.rpush(ingress_list, item)
        counter += 1
    return JSONResponse(content=counter)
