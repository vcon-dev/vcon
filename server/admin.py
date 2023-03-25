import importlib
from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
from load_config import (
    load_config,
)
import redis_mgr
from pydantic import BaseModel
import vcon
import json
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
vcon_redis = VconRedis()

logger = init_logger(__name__)
logger.info("admin portal")
app = FastAPI.conserver_app
from fastapi import FastAPI, File, UploadFile
from fastapi import FastAPI, Form
import datetime

class InputParams(BaseModel):
    name1: str
    name2: str
    tel1: str
    tel2: str
    ingress_list: str

@app.post("/create_vcon")
async def create_vcon(name1: str = Form(), 
                name2: str = Form(), 
                tel1: str = Form(),  
                tel2: str = Form(),
                ingress_list: str = Form(),
                filename: UploadFile = File(...)):
    
    v = vcon.Vcon()
    v.set_uuid("vcon.dev") # Use your own domain name and stop polluting ours.
    v.add_party({
        "tel": tel1,
        "name": name1
    })
    v.add_party({
        "tel": tel2,
        "name": name2
    })
    v.add_dialog_inline_recording(filename.file.read(), 
                                  datetime.datetime.now(), 
                                  duration=0,
                                  parties=[0,1], 
                                  mime_type=vcon.Vcon.MIMETYPE_AUDIO_WAV, 
                                  file_name=filename.filename)


    await vcon_redis.store_vcon(v)

    # If supplied, push the vCon onto the ingress list
    if ingress_list: 
        r = await redis_mgr.get_client()
        await r.lpush("ingress_list", v.uuid)

    return f"vCon {v.uuid} created"

