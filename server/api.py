import sys
import logging
import logging.config
import redis.asyncio as redis
from redis.commands.json.path import Path
import simplejson as json

from fastapi import status
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.applications import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import json
from settings import REDIS_URL, HOSTNAME

# Our local modules``
sys.path.append("..")
import vcon

logger = logging.getLogger(__name__)
logging.config.fileConfig('./logging.conf')
logger.info('Conserver starting up')


# Setup redis
r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

# Load FastAPI app
app = FastAPI.conserver_app


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
VCON_VERSION = "0.1.1"
MIMETYPE="audio/wav"

async def last_vcons(size=200):
    try:
        vcons = []
        vcon_ids = await r.lrange("call_log_list", 0, size)
        for vcon_uuid in vcon_ids:
            print("vcon_uuid being added ", vcon_uuid)
            inbound_vcon = await r.json().get("vcon-{}".format(vcon_uuid), Path.root_path())
            if inbound_vcon:
                vcons.append(inbound_vcon)
        return vcons
    except Exception as e:
        logger.error(e)
        return []


# Home page route
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    vcons = await last_vcons()
    return templates.TemplateResponse("index.html", {"request": request, "vCons": vcons})


@app.get(
    "/vcon/{vConUuid}"
)
async def show_vcon(request: Request, vConUuid: str):
    try:
        key = "vcon-{}".format(vConUuid)
        vCon = await r.json().get(key, Path.root_path())
        return JSONResponse(status_code=status.HTTP_200_OK, content=vCon)  
    except Exception as e:
        logger.error("Error loading vCon from Redis: %s", e)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND)


@app.get("/details/{vConUuid}", response_class=HTMLResponse)
async def show_vcon_details(request: Request, vConUuid: str):
    try:
        key = "vcon-{}".format(vConUuid)
        vcon_details = await r.json().get(key, Path.root_path())
        # This vCon object might be packed, so unpack it
        vCon = vcon.Vcon()
        vCon.loads(json.dumps(vcon_details))

        for index, dialog in enumerate(vCon.dialog): 
            if dialog['type'] != 'recording':
                continue
            # Save this recording to a file
            bytes = vCon.decode_dialog_inline_body(index) 
            with open("static/{}".format(dialog['filename']), "wb") as f:
                f.write(bytes)
            vcon_details['dialog'][index]['url'] = HOSTNAME + "/static/{}".format(dialog['filename'])


        return templates.TemplateResponse("vcon.html", {"request": request, "vcon": vcon_details})
    except Exception as e:
        logger.error("Error loading vCon from Redis: %s", e)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND)
