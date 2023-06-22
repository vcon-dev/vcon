import sys
import asyncio
from lib.logging_utils import init_logger
from datetime import datetime
from fastapi import HTTPException
from fastapi.applications import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from uuid import UUID
from pydantic import BaseModel, Json, Field
from fastapi.responses import JSONResponse
import importlib
from redis.commands.json.path import Path
import typing
import enum
import pyjq
from typing import List
import tqdm
import json
from datetime import datetime
import redis
import redis.commands.search.aggregation as aggregations
from redis.commands.search.aggregation import Asc
from urllib.parse import quote, unquote
import redis_mgr

from peewee import *
from playhouse.postgres_ext import *
from settings import VCON_STORAGE
import logging
logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


if VCON_STORAGE:
    class VConModel(Model):
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
            
class Chain(BaseModel):
    links: typing.List[str] = []
    ingress_lists: typing.List[str] = []
    storage: typing.List[str] = []
    egress_lists: typing.List[str] = []
    enabled: int = 1

class Link(BaseModel):
    module: str
    options: typing.Dict[str, typing.Any] = {}
    ingress_lists: typing.List[str] = []
    egress_lists: typing.List[str] = []

class Storage(BaseModel):
    module: str
    options: typing.Dict[str, typing.Any] = {}


class Party(BaseModel):
    tel: str = None
    stir: str = None
    mailto: str = None
    name: str = None
    validation: str = None
    jcard: str = None
    gmlpos: str = None
    civicaddress: str = None
    timezone: str = None


class DialogType(str, enum.Enum):
    recording = "recording"
    text = "text"


class Dialog(BaseModel):
    type: DialogType
    start: typing.Union[int, str, datetime]
    duration: float = None
    parties: typing.Union[int, typing.List[typing.Union[int, typing.List[int]]]]
    mimetype: str = None
    filename: str = None
    body: str = None
    url: str = None
    encoding: str = None
    alg: str = None
    signature: str = None


class Analysis(BaseModel):
    type: str
    dialog: int
    mimetype: str = None
    filename: str = None
    vendor: str = None
    _schema: str = None
    body: str = None
    encoding: str = None
    url: str = None
    alg: str = None
    signature: str = None


class Attachment(BaseModel):
    type: str
    party: int = None
    mimetype: str = None
    filename: str = None
    body: str = None
    encoding: str = None
    url: str = None
    alg: str = None
    signature: str = None


class Group(BaseModel):
    uuid: UUID
    body: str = None
    encoding: str = None
    url: str = None
    alg: str = None
    signature: str = None


class Vcon(BaseModel):
    vcon: str
    uuid: UUID
    created_at: typing.Union[int, str, datetime]
    subject: str = None
    redacted: dict = None
    appended: dict = None
    group: typing.List[Group] = []
    parties: typing.List[Party] = []
    dialog: typing.List[Dialog] = []
    analysis: typing.List[Analysis] = []
    attachments: typing.List[Attachment] = []


# Our local modules``
sys.path.append("..")

logger = init_logger(__name__)
logger.info("Conserver starting up")


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


@app.get("/vcon", response_model=List[str])
async def get_vcons(page: int = 1, size: int = 50, since: datetime = None, until: datetime = None):
    """ 
    Gets the UUIDs of conversations between the given dates, sorted by date desc.
    Use/vcon/{uuid} to retreive the full text of the vCon.  
    Use page, size, since, and until parameters to paginate the results.
    """
    if VCON_STORAGE:
        offset = (page - 1) * size
        query = VConModel.select()
        if since:
            query = query.where(VConModel.created_at > since)
        if until:
            query = query.where(VConModel.created_at < until)
        query = query.order_by(VConModel.created_at.desc()).offset(offset).limit(size)
        r = [str(vcon.uuid) for vcon in query]
        return r

    else:
        # Assumes that the REDIS database has a full-text index called "vconIdx"
        r = redis_mgr.get_client()
        index_name = 'vconIdx'
        try:
            indexInfo  = await r.ft(index_name).info()
        except redis.exceptions.ResponseError:
            print("Must have the index " + index_name + " in the database")
            exit(1)

        # Get the last vcon from the database
        # if the since or until params are set, then add this to the redis query
        if since:
            q += " @created_at:[{} +inf]".format(since.timestamp())
        if until:
            q += " @created_at:[-inf {}]".format(until.timestamp())
        

        req = aggregations.AggregateRequest(query=q).sort_by(Asc("@created_at")).limit((page-1)*size, size)
        req.load('$')
        results = await r.ft(index_name).aggregate(req)

        uuids = []
        for row in tqdm.tqdm(results.rows):
            vcon = json.loads(row[1].decode("UTF-8"))
            uuids.append(str(vcon['uuid']))
        return uuids

@app.get("/vcon/{vcon_uuid}")
async def get_vcon(vcon_uuid: UUID):
    if VCON_STORAGE:
        q = VConModel.select().where(VConModel.uuid == vcon_uuid)
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


@app.get("/vcon/{vcon_uuid}/jq")
async def get_vcon_jq_transform(vcon_uuid: UUID, jq_transform):
    try:
        logger.info("jq transform string: {}".format(jq_transform))
        r = redis_mgr.get_client()
        vcon = await r.json().get(f"vcon:{str(vcon_uuid)}")
        query_result = pyjq.all(jq_transform, vcon)
        logger.debug("jq  transform result: {}".format(query_result))
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None

    return JSONResponse(content=query_result)


@app.get("/vcon/{vcon_uuid}/JSONPath", response_model=List[Party])
async def get_vcon_json_path(vcon_uuid: UUID, path_string: str):
    try:
        logger.info("JSONPath query string: {}".format(path_string))
        r = redis_mgr.get_client()
        query_result = await r.json().get(f"vcon:{str(vcon_uuid)}", path_string)
        logger.debug("JSONPath query result: {}".format(query_result))
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return JSONResponse(content=query_result)

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
        vcon = VConModel.create(
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
            await r.json().set(f"vcon:{str(dict_vcon['uuid'])}", "$", dict_vcon)
        except Exception as e:
            logger.info("Error: {}".format(e))
            return None
        logger.debug("Posted vcon  {} len {}".format(inbound_vcon.uuid, len(dict_vcon)))
        return JSONResponse(content=dict_vcon)


@app.put("/vcon/{vcon_uuid}")
async def put_vcon(vcon_uuid: UUID, inbound_vcon: Vcon):
    try:
        r = redis_mgr.get_client()
        dict_vcon = inbound_vcon.dict()
        dict_vcon["uuid"] = str(inbound_vcon.uuid)
        await r.json().set(f"vcon:{str(dict_vcon['uuid'])}", "$", dict_vcon)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return JSONResponse(content=dict_vcon)


@app.patch("/vcon/{vcon_uuid}", response_model=Vcon)
async def patch_vcon(vcon_uuid: UUID, plugin: str):
    r = redis_mgr.get_client()
    try:
        plugin_module = importlib.import_module(plugin)
        await asyncio.create_task(plugin_module.run(vcon_uuid))
    except Exception as e:
        message = "Error in plugin: {} {}".format(plugin, e)
        logger.info(message)
        raise HTTPException(
            status_code=500, detail="server error in plugin: {}".format(plugin)
        )

    dict_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())

    if dict_vcon is None:
        message = "Error: patch plugin results for Vcon {} not found".format(vcon_uuid)
        logger.info(message)
        raise HTTPException(
            status_code=500,
            detail="server error, no result from plugin: {}".format(plugin),
        )

    return JSONResponse(content=dict_vcon)


@app.delete("/vcon/{vcon_uuid}")
async def delete_vcon(vcon_uuid: UUID, status_code=204):
    try:
        r = redis_mgr.get_client()
        await r.delete(f"vcon:{str(vcon_uuid)}")
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

@app.get("/chain")
async def get_chains():
    try:
        r = redis_mgr.get_client()
        keys = await r.keys("chain:*")
        chains = {}
        for key in keys:
            chain = await r.json().get(key, "$")
            key_name = key.decode().split(":")[1]
            chains[key_name] = chain
        return JSONResponse(content=chains)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None

@app.get("/chain/{chain_name}")
async def get_chain(chain_name: str):
    try:
        r = redis_mgr.get_client()
        chain = await r.json().get(f"chain:{chain_name}", "$")
        return JSONResponse(content=chain)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    
@app.post("/chain")
async def post_chain(inbound_chain: Chain):
    try:
        r = redis_mgr.get_client()
        dict_chain = inbound_chain.dict()
        await r.json().set(f"chain:{str(dict_chain['name'])}", "$", dict_chain)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    logger.debug("Posted chain  {} len {}".format(inbound_chain.name, len(dict_chain)))
    return JSONResponse(content=dict_chain)

@app.put("/chain/{chain_name}")
async def put_chain(chain_name: str, inbound_chain: Chain):
    try:
        r = redis_mgr.get_client()
        dict_chain = inbound_chain.dict()
        await r.json().set(f"chain:{str(dict_chain['name'])}", "$", dict_chain)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return JSONResponse(content=dict_chain)

@app.delete("/chain/{chain_name}")
async def delete_chain(chain_name: str, status_code=204):
    try:
        r = redis_mgr.get_client()
        await r.delete(f"chain:{str(chain_name)}")
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

@app.get("/link")
async def get_links():
    try:
        r = redis_mgr.get_client()
        keys = await r.keys("link:*")
        links = {}
        for key in keys:
            link = await r.json().get(key, "$")
            key_name = key.decode().split(":")[1]
            links[key_name] = link
        return JSONResponse(content=links)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    
@app.get("/link/{link_name}")
async def get_link(link_name: str):
    try:
        r = redis_mgr.get_client()
        link = await r.json().get(f"link:{link_name}", "$")
        return JSONResponse(content=link)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    
@app.post("/link")
async def post_link(inbound_link: Link):
    try:
        r = redis_mgr.get_client()
        dict_link = inbound_link.dict()
        await r.json().set(f"link:{str(dict_link['name'])}", "$", dict_link)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    logger.debug("Posted link  {} len {}".format(inbound_link.name, len(dict_link)))
    return JSONResponse(content=dict_link)

@app.put("/link/{link_name}")
async def put_link(link_name: str, inbound_link: Link):
    try:
        r = redis_mgr.get_client()
        dict_link = inbound_link.dict()
        await r.json().set(f"link:{str(dict_link['name'])}", "$", dict_link)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return JSONResponse(content=dict_link)

@app.delete("/link/{link_name}")
async def delete_link(link_name: str, status_code=204):
    try:
        r = redis_mgr.get_client()
        await r.delete(f"link:{str(link_name)}")
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

@app.get("/storage")
async def get_storages():
    try:
        r = redis_mgr.get_client()
        keys = await r.keys("storage:*")
        storages = {}
        for key in keys:
            storage = await r.json().get(key, "$")
            key_name = key.decode().split(":")[1]
            storages[key_name] = storage
        return JSONResponse(content=storages)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    
@app.get("/storage/{storage_name}")
async def get_storage(storage_name: str):
    try:
        r = redis_mgr.get_client()
        storage = await r.json().get(f"storage:{storage_name}", "$")
        return JSONResponse(content=storage)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    
@app.post("/storage")
async def post_storage(inbound_storage: Storage):
    try:
        r = redis_mgr.get_client()
        dict_storage = inbound_storage.dict()
        await r.json().set(f"storage:{str(dict_storage['name'])}", "$", dict_storage)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    logger.debug("Posted storage  {} len {}".format(inbound_storage.name, len(dict_storage)))
    return JSONResponse(content=dict_storage)

@app.put("/storage/{storage_name}")
async def put_storage(storage_name: str, inbound_storage: Storage):
    try:
        r = redis_mgr.get_client()
        dict_storage = inbound_storage.dict()
        await r.json().set(f"storage:{str(dict_storage['name'])}", "$", dict_storage)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return JSONResponse(content=dict_storage)

@app.delete("/storage/{storage_name}")
async def delete_storage(storage_name: str, status_code=204):
    try:
        r = redis_mgr.get_client()
        await r.delete(f"storage:{str(storage_name)}")
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

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

def add_ts(r, key):
    vcon = r.json().get(key)
    # Convert "created_at" to timestamp
    created_at = vcon['created_at']
    created_at_ts = datetime.fromisoformat(created_at).timestamp()

    # Add "created_at_ts" to the JSON
    vcon['created_at_ts'] = created_at_ts
    r.json().set(key, "$", vcon)

@app.on_event("startup")
async def startup_event():
    if False:
        r = redis.Redis(host='localhost', port=6379, db=0)
        keys = r.keys("vcon:*")
        for key in tqdm.tqdm(keys):
            add_ts(r,key)
        r.close()