import traceback
from datetime import datetime
from typing import Dict, List, Union, Optional
from uuid import UUID

import redis_mgr
from fastapi import FastAPI, HTTPException, Query
from fastapi.routing import Lifespan
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from lib.logging_utils import init_logger
from load_config import load_config
from config import Configuration
from storage.base import Storage
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
from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


logger = init_logger(__name__)
logger.info("Api starting up")


# Load FastAPI app
app = FastAPI()
redis_async = None


async def on_startup():
    global redis_async
    redis_async = await redis_mgr.get_async_client()


async def on_shutdown():
    await redis_async.close()

app.router.add_event_handler("startup", on_startup)
app.router.add_event_handler("shutdown", on_shutdown)
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
    meta: Optional[dict] = {}


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
async def get_vcons_uuids(
    page: int = 1, size: int = 50, since: datetime = None, until: datetime = None
):
    # Redis is storing the vCons. Use the vcons sorted set to get the vCon UUIDs
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
    vcon = await redis_async.json().get(f"vcon:{str(vcon_uuid)}")
    if not vcon:
        # Fallback to the storages if the vcon is not found in redis
        for storage_name in Configuration.get_storages():
            vcon = Storage(storage_name=storage_name).get(vcon_uuid)
            if vcon:
                break

    return JSONResponse(content=vcon, status_code=200 if vcon else 404)


@app.get(
    "/vcons",
    response_model=Vcon,
    summary="Gets vCons by UUIDs",
    description="Get multiple vCons by UUIDs",
    tags=["vcon"],
)
async def get_vcons(vcon_uuids: List[UUID] = Query(None)):
    keys = [f"vcon:{vcon_uuid}" for vcon_uuid in vcon_uuids]
    vcons = await redis_async.json().mget(keys=keys, path=".")

    results = []
    for vcon_uuid, vcon in zip(vcon_uuids, vcons):
        if not vcon:
            # Fallback to the storages if the vcon is not found in redis
            for storage_name in Configuration.get_storages():
                vcon = Storage(storage_name=storage_name).get(vcon_uuid)
                if vcon:
                    break
        results.append(vcon)

    return JSONResponse(content=results, status_code=200)

class SearchResult(BaseModel):
    uuid: str
    created_at: datetime
    updated_at: Optional[datetime]
    subject: Optional[str]
    parties: List[dict]

@app.get(
    "/vcons/search",
    response_model=List[SearchResult],
    summary="Search vCons based on various parameters",
    description="Search for vCons using personal identifiers and metadata.",
    tags=["vcon"],
)
async def search_vcons(
    tel: Optional[str] = Query(None, description="Phone number to search for"),
    mailto: Optional[str] = Query(None, description="Email address to search for"),
    name: Optional[str] = Query(None, description="Name of the party to search for"),
):
    try:
        # Check if tel, mailto, and name are all None
        if tel is None and mailto is None and name is None:
            raise HTTPException(status_code=400, detail="At least one search parameter must be provided")
        
        # Debug logging 
        print("tel: {}".format(tel))
        print("mailto: {}".format(mailto))
        print("name: {}".format(name))
        
        # Each of the search parameters has a corresponding Redis key that
        # contains the set of vCon UUIDs that match the search parameter
        keys = []
        if tel:
            # Look into REDIS for keys that match the phone number and take the 
            # uuids from those keys
            tel_key = f"tel:{tel}"
            # Get the members of this set, and add them to the keys list
            uuids = await redis_async.smembers(tel_key)
            print("Found {} uuids for tel: {}".format(len(uuids), tel))
            print("uuids: {}".format(uuids))
            
            # Add the uuids to the keys list, with each uuid prefixed with "vcon:"
            for uuid in uuids:
                keys.append(f"vcon:{uuid}")
                print("Adding key: {}".format(f"vcon:{uuid}"))
                
        if mailto:
            # Look into REDIS for keys that match the email and take the 
            # uuids from those keys
            mailto_key = f"mailto:{mailto}"
            # Get the members of this set, and add them to the keys list
            uuids = await redis_async.smembers(mailto_key)
            print("Found {} uuids for mailto: {}".format(len(uuids), mailto))
            print("uuids: {}".format(uuids))
            
            # Add the uuids to the keys list, with each uuid prefixed with "vcon:"
            for uuid in uuids:
                keys.append(f"vcon:{uuid}")
                print("Adding key: {}".format(f"vcon:{uuid}"))
                            
        if name:
            # Look into REDIS for keys that match the name and take the 
            # uuids from those keys
            name_key = f"name:{name}"
            # Get the members of this set, and add them to the keys list
            uuids = await redis_async.smembers(name_key)
            print("Found {} uuids for name: {}".format(len(uuids), name))
            print("uuids: {}".format(uuids))
            print(type(uuids))
            print(uuids)
            for uuid in uuids:
                keys.append(f"vcon:{uuid}")
                print("Adding key: {}".format(f"vcon:{uuid}"))
                
            
        # Get the results for each key
        print("keys: {}".format(keys))
        print(type(keys))
        print(keys)
        

        results = await redis_async.json().mget(keys=keys, path=".")
        
        print("results: {}".format(results))
        print(type(results))
        
        # Each key 
        # Process and return the results
        return [
            SearchResult(
                uuid=result['uuid'],
                created_at=result['created_at'],
                updated_at=result.get('updated_at'),
                subject=result.get('subject'),
                parties=result['parties']
            )
            for result in results
        ]

    except Exception as e:
        logger.error(f"Error in search_vcons: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during the search")


@app.post(
    "/vcon",
    response_model=Vcon,
    summary="Inserts a vCon into the database",
    description="How to insert a vCon into the database.",
    tags=["vcon"],
)
async def post_vcon(inbound_vcon: Vcon):
    try:
        print(type(inbound_vcon))
        dict_vcon = inbound_vcon.model_dump()
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
        
        # Index the parties 
        logger.debug("Adding vcon {} to parties sets".format(inbound_vcon.uuid))
        await index_vcon(inbound_vcon.uuid)
        
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
    "/dlq/reprocess",
    status_code=200,
    summary="Reprocess the dead letter queue",
    description="Move the dead letter queue vcons back to the ingress chain",
    tags=["dlq"],
)
async def post_dlq_reprocess(ingress_list: str):
    # Get all items from redis list and move them back to the ingress list
    dlq_name = get_ingress_list_dlq_name(ingress_list)
    counter = 0
    while item := await redis_async.rpop(dlq_name):
        await redis_async.rpush(ingress_list, item)
        counter += 1
    return JSONResponse(content=counter)


@app.get(
    "/dlq",
    status_code=200,
    summary="Get Vcons list from the dead letter queue",
    description="Get Vcons list from the dead letter queue, returns array of vcons.",
    tags=["dlq"],
)
async def get_dlq_vcons(ingress_list: str):
    """ Get all the vcons from the dead letter queue """
    dlq_name = get_ingress_list_dlq_name(ingress_list)
    vcons = await redis_async.lrange(dlq_name, 0, -1)
    return JSONResponse(content=vcons)


async def index_vcon(uuid):
    key = "vcon:"+uuid
    vcon = await redis_async.json().get(key)
    created_at = datetime.fromisoformat(vcon["created_at"])
    timestamp = int(created_at.timestamp())
    vcon_uuid = vcon["uuid"]
    await add_vcon_to_set(key, timestamp)

    # We would also like to search vCons by the tel number in each dialog.
    for party in vcon["parties"]:
        if party.get('tel', None):
            tel = party["tel"]
            tel_key = f"tel:{tel}"
            await redis_async.sadd(tel_key, vcon_uuid)
        if party.get('mailto', None):
            mailto = party["mailto"]
            mailto_key = f"mailto:{mailto}"
            await redis_async.sadd(mailto_key,  vcon_uuid)
        if party.get('name', None):
            name = party["name"]
            name_key = f"name:{name}"
            await redis_async.sadd(name_key, vcon_uuid)
            
@app.get(
    "/index_vcons",
    status_code=200,
    summary="Forces a reset of the vcon search list",
    description="Forces a reset of the vcon search list, returns the number of vCons indexed.",
    tags=["config"],
)
async def index_vcons():
    try:
        # Get all of the vcon keys, and add them to the sorted set
        vcon_keys = await redis_async.keys("vcon:*")
        for key in vcon_keys:
            uuid = key.split(":")[1]
            await index_vcon(uuid)
                
        # Get all of the vcon keys, and add them to the sorted set
        
        # Return the number of vcons indexed
        return JSONResponse(content=len(vcon_keys))
            
    except Exception as e:
        logger.info("Error: {}".format(e))
        raise HTTPException(status_code=500)


