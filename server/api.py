import logging
import sys
from datetime import datetime
from typing import Dict, List, Union
from uuid import UUID

import redis_mgr
import tqdm
from fastapi.applications import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from lib.logging_utils import init_logger
from load_config import load_config
from peewee import *
from playhouse.postgres_ext import *
from pydantic import BaseModel
from settings import VCON_STORAGE, VCON_SORTED_FORCE_RESET, VCON_SORTED_SET_NAME
from starlette.staticfiles import StaticFiles

# Our local modules``
sys.path.append("..")
logger = init_logger(__name__)
logger.info("API starting up")

# Load FastAPI app
app = FastAPI.conserver_app
app.mount("/static", StaticFiles(directory="static"), name="static")
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
    subject: str = None
    redacted: dict = None
    appended: dict = None
    group: List[Dict] = []
    parties: List[Dict] = []
    dialog: List[Dict] = []
    analysis: List[Dict] = []
    attachments: List[Dict] = []

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
    r = redis_mgr.get_client()
    await r.zadd(VCON_SORTED_SET_NAME, {vcon_uuid: timestamp})

@app.on_event("startup")
async def startup_event():
    if VCON_STORAGE:
        # Use peewee to connect to the database and create the table if 
        # we are supporting an external database
        # This is how we manage the expiration of keys in REDIS
        # We use a postgres database to store the vcon data
        logger.info("Using external database {}".format(VCON_STORAGE))
    else:
        # Use redis to store the vcon data
        # Use a sorted set, with the created_at field as the score, so that we can
        # sort the results by date.  Convert the created_at field to a unix timestamp
        logger.info("Using redis database")
        sorted_set = VCON_SORTED_SET_NAME

        # On startup, iterate over all the vCon keys in the database, and add them to the sorted set
        # This is a one-time operation, so we can do it synchronously
        # CHeck to see if we need to reset the sorted set
        r = redis_mgr.get_client()
        if VCON_SORTED_FORCE_RESET == "true" or await r.zcard(sorted_set) == 0:
            logger.info("Resetting the sorted set")
            # Delete the sorted set
            await r.delete(sorted_set)
            vcon_keys = await r.keys("vcon:*")

            logger.info("Adding {} vcons to the sorted set".format(len(vcon_keys)))
            for vcon_key in tqdm.tqdm(vcon_keys):
                vcon = await r.json().get(vcon_key)
                # Convert the ISO string to a unix timestamp
                created_at = datetime.fromisoformat(vcon['created_at'])
                timestamp = int(created_at.timestamp())
                await add_vcon_to_set(vcon_key, timestamp)

# These are the vCon data models
@app.get("/vcon", response_model=List[str])
async def get_vcons(page: int = 1, size: int = 50, since: datetime = None, until: datetime = None):
    """ 
    Gets the UUIDs of conversations between the given dates, sorted by date desc.
    Use/vcon/{uuid} to retreive the full text of the vCon.  
    Use page, size, since, and until parameters to paginate the results.
    """
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
        vcon_uuids = await r.zrevrangebyscore(VCON_SORTED_SET_NAME, until_timestamp, since_timestamp, start=offset, num=size)

        # Convert the vcon_uuids to strings and strip the vcon: prefix
        vcon_uuids = [vcon.decode("utf-8").split(":")[1] for vcon in vcon_uuids]
        return vcon_uuids
        
@app.get("/vcon/{vcon_uuid}")
async def get_vcon(vcon_uuid: UUID):
    if VCON_STORAGE:
        q = VConPeeWee.select().where(VConPeeWee.uuid == vcon_uuid)
        r = q.get()
        return JSONResponse(content=r.vcon_json)
    else:
        try:
            r = redis_mgr.get_client()
            vcon = await r.json().get(f"vcon:{str(vcon_uuid)}")
        except Exception as e:
            logger.info("Error: {}".format(e))
            return None
        logger.debug(
            "Returning whole vcon for {} found: {}".format(vcon_uuid, vcon is not None)
        )
        return JSONResponse(content=vcon)

@app.post("/vcon")
async def post_vcon(inbound_vcon: Vcon):
    if VCON_STORAGE:
        # Create a new vcon in the database
        # Use peewee
        id = inbound_vcon.uuid
        vcon_json = inbound_vcon.json()
        uuid = inbound_vcon.uuid
        created_at = inbound_vcon.created_at
        updated_at = inbound_vcon.updated_at or inbound_vcon.created_at
        subject = inbound_vcon.subject
        type = inbound_vcon.type
        vcon = VConPeeWee.create(
            id=id,
            uuid=uuid,
            created_at=created_at,
            updated_at=updated_at,
            subject=subject,
            type=type,
            vcon_json=vcon_json,
        )
        return JSONResponse(content=inbound_vcon.dict())
    else:
        try:
            r = redis_mgr.get_client()
            dict_vcon = inbound_vcon.dict()
            dict_vcon["uuid"] = str(inbound_vcon.uuid)
            key = f"vcon:{str(dict_vcon['uuid'])}"
            created_at = datetime.fromisoformat(dict_vcon['created_at'])
            timestamp = int(created_at.timestamp())

            await r.json().set(key, "$", dict_vcon)
            await add_vcon_to_set(key, timestamp)
        except Exception as e:
            logger.info("Error: {}".format(e))
            return None
        logger.debug("Posted vcon  {} len {}".format(inbound_vcon.uuid, len(dict_vcon)))
        return JSONResponse(content=dict_vcon)

@app.delete("/vcon/{vcon_uuid}")
async def delete_vcon(vcon_uuid: UUID, status_code=204):
    # FIX: support the VCON_STORAGE case
    try:
        r = redis_mgr.get_client()
        await r.delete(f"vcon:{str(vcon_uuid)}")
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

# Ingress and egress endpoints for vCon IDs
# Create an endpoint to push vcon IDs to one or more redis lists
@app.post("/vcon/ingress")
async def post_vcon_ingress(vcon_uuids: List[str], ingress_list: str, status_code=204):
    try:
        r = redis_mgr.get_client()
        for vcon_uuid in vcon_uuids:
            await r.lpush(ingress_list, vcon_uuid)
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

# Create an endpoint to pop vcon IDs from one or more redis lists
@app.get("/vcon/egress")
async def get_vcon_engress(egress_list: str, limit=1, status_code=200):
    try:
        r = redis_mgr.get_client()
        vcon_uuids = []
        for i in range(limit):
            vcon_uuid = await r.rpop(egress_list)
            if vcon_uuid:
                vcon_uuids.append(vcon_uuid)
        return JSONResponse(content=vcon_uuids)

    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

# Create an endpoint to count the number of vCon UUIds in a redis list
@app.get("/vcon/count")
async def get_vcon_count(egress_list: str, status_code=200):
    try:
        r = redis_mgr.get_client()
        count = await r.llen(egress_list)
        return JSONResponse(content=count)

    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

@app.get("/config")
async def get_config(status_code=200):
    try:
        r = redis_mgr.get_client()
        config = await r.json().get("config_file")
        return JSONResponse(content=config)

    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

# THis endpoint is used to update the config file, then calls
# the load_config endpoint to load the new config file into redis
@app.post("/config")
async def post_config(config: Dict, status_code=204):
    try:
        await load_config(config)
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

# This endpoint clears the config
@app.delete("/config")
async def delete_config(status_code=204):
    try:
        r = redis_mgr.get_client()
        await r.delete("config")
        # Delete the links
        links = await r.keys("link:*")
        for link in links:
            await r.delete(link)
        # Delete the storages
        storages = await r.keys("storage:*")
        for storage in storages:
            await r.delete(storage)
        # Delete the chains
        chains = await r.keys("chain:*")
        for chain in chains:
            await r.delete(chain)
            
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code