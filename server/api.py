import sys
import os
import asyncio
import logging
import logging.config
from datetime import datetime
from fastapi.applications import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from settings import REDIS_URL
import redis.asyncio as redis
from uuid import UUID
from pydantic import BaseModel, Json
from fastapi_pagination import Page, add_pagination, paginate
from fastapi.responses import JSONResponse
import importlib
from redis.commands.json.path import Path
import typing
import enum

class Party(BaseModel):
    tel: str = None
    stir: str = None
    mailto: str = None
    name: str = None
    validation: str = None
    jcard: Json = None
    gmlpos: str = None
    civicaddress: str = None
    timezone: str = None

class DialogType(enum.Enum):
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
    body: Json = None
    encoding: str = None
    url: str = None
    alg: str = None
    signature: str = None


class Vcon(BaseModel):
    vcon: str
    uuid: UUID
    created_at: typing.Union[int, str, datetime] = datetime.now().timestamp()
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

logger = logging.getLogger(__name__)
logger.info('Conserver starting up')


# Setup redis
r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

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

@app.get('/vcon', response_model=Page[str])
async def get_vcons():
    keys = await r.keys("vcon:*")
    uuids = [ key.replace("vcon:", "") for key in keys ]
    return paginate(uuids)

@app.get('/vcon/{vcon_uuid}')
async def get_vcon(vcon_uuid: UUID):
    try:
        vcon = await r.json().get(f"vcon:{str(vcon_uuid)}")
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return JSONResponse(content=vcon)

@app.get('/vcon/{vcon_uuid}/party', response_model=Page[Party])
async def get_parties(vcon_uuid: UUID):
    try:
        parties = await r.json().get(f"vcon:{str(vcon_uuid)}", '$.parties')
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return paginate(parties[0])

@app.get('/vcon/{vcon_uuid}/dialog', response_model=Page[Dialog])
async def get_dialogs(vcon_uuid: UUID):
    try:
        dialogs = await r.json().get(f"vcon:{str(vcon_uuid)}", '$.dialog')
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return paginate(dialogs[0])

@app.get('/vcon/{vcon_uuid}/analysis', response_model=Page[Analysis])
async def get_analyses(vcon_uuid: UUID):
    try:
        analyses = await r.json().get(f"vcon:{str(vcon_uuid)}", '$.analysis')
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return paginate(analyses[0])

@app.get('/vcon/{vcon_uuid}/attachment', response_model=Page[Attachment])
async def get_attachments(vcon_uuid: UUID):
    try:
        attachments = await r.json().get(f"vcon:{str(vcon_uuid)}", '$.attachments')
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return paginate(attachments[0])
add_pagination(app)

@app.post('/vcon')
async def post_vcon(inbound_vcon: Vcon):
    try:
        dict_vcon = inbound_vcon.dict()
        dict_vcon['uuid'] = str(inbound_vcon.uuid)
        await r.json().set(f"vcon:{str(dict_vcon['uuid'])}", "$", dict_vcon)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return JSONResponse(content=dict_vcon)

@app.put('/vcon/{vcon_uuid}')
async def put_vcon(vcon_uuid: UUID, inbound_vcon: Vcon):
    try:
        dict_vcon = inbound_vcon.dict()
        dict_vcon['uuid'] = str(inbound_vcon.uuid)
        await r.json().set(f"vcon:{str(dict_vcon['uuid'])}", "$", dict_vcon)
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    return JSONResponse(content=dict_vcon)

@app.patch('/vcon/{vcon_uuid}', response_model=Vcon)
async def patch_vcon(vcon_uuid: UUID, plugin: str):
    try:
        plugin_module = importlib.import_module(plugin)
        await asyncio.create_task(plugin_module.run(vcon_uuid))
    except Exception as e:
        logger.info("Error: {}".format(e))
        return None
    dict_vcon = await r.json().get(f"vcon:{str(vcon_uuid)}", Path.root_path())
    return JSONResponse(content=dict_vcon)

@app.delete('/vcon/{vcon_uuid}')
async def delete_vcon(vcon_uuid: UUID, status_code=204):
    try:
        await r.delete(f"vcon:{str(vcon_uuid)}")
    except Exception as e:
        logger.info("Error: {}".format(e))
        status_code = 500
    return status_code

