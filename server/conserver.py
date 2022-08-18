
import os
import sys
import logging
from typing import Optional, List
import json
import urllib.request
import asyncio
from fastapi import status
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.applications import FastAPI
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from pydub import AudioSegment
from deepgram import Deepgram
import motor.motor_asyncio
import json
import jose.utils
import jose.jws
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

from pydantic_models import VconModel, PyObjectId

# Our local modules
sys.path.append("..")
import vcon

# Load FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("ui")
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Start third-party services
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.conserver
loop = asyncio.get_event_loop()

# Environment variables
VCON_VERSION = "0.1.1"
DEEPGRAM_KEY = os.environ["DEEPGRAM_KEY"]
MIMETYPE="audio/wav"


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    vcons = await db["vcons"].find().to_list(100)
    return templates.TemplateResponse("index.html", {"request": request, "vCons": vcons})


# This is the endpoint for the vcon creation that comes from
# the SNS topic
@app.post("/vcon", response_class=HTMLResponse)
async def post_vcon(request: Request):
    ingress_vcon = await request.json()
    print(json.dumps(ingress_vcon, indent=4, sort_keys=True))

    # Construct empty vCon
    vCon = vcon.Vcon()

    # Add some basic call META data
    caller = ingress_vcon["payload"]["cdr"]["src"]
    called = ingress_vcon["payload"]["cdr"]["dst"]
    vCon.set_party_tel_url(caller)
    vCon.set_party_tel_url(called)

    recording_url = ingress_vcon["payload"]["recording"]["url"]
    # Remove query string
    host = recording_url.split("?")[0]
    # The file name is the last part of the URL
    recording_filename = host.split("/")[-1]

    # Add a recording of the call
    print("Reading recording from", recording_url)

    recording_bytes = urllib.request.urlopen(recording_url).read()
    vCon.add_dialog_inline_recording(
    recording_bytes,
    ingress_vcon["payload"]["cdr"]["starttime"],
    ingress_vcon["payload"]["cdr"]["duration"],
    [0, 1], # parties recorded
    "audio/x-wav", # MIME type
    recording_filename)

    # Save the original RingPlan JSON in the vCon
    vCon.attachments.append(ingress_vcon)

    # Save the vCon to the database
    print(type(vCon))
    json_string = vCon.dumps()
    vcon_dict = json.loads(json_string)
    vCon_id = await db["vcons"].insert_one(vcon_dict)
    print(vCon_id)
    return JSONResponse(status_code=status.HTTP_200_OK)

@app.get(
    "/vcon", response_description="List all vcons", response_model=List[VconModel]
)
async def list_vcons():
    vcons = await db["vcons"].find().to_list(100)
    return vcons


@app.get(
    "/vcon/{id}", response_description="Computer Readable vCon", response_model=VconModel
)
async def show_vcon(request: Request, id: PyObjectId):
    vcon = await db["vcons"].find_one({"_id": id})
    return vcon  

@app.get("/details/{id}", response_description="Web site vCon", response_class="text/html")
async def show_vcon(request: Request, id: PyObjectId):
    vcon = await db["vcons"].find_one({"_id": id})
    _id = str(vcon['_id'])
    dialog = vcon['dialog'][0]
    wav_filename = "static/{}.wav".format(_id)
    mp3_filename = "static/{}.mp3".format(_id)
    decoded_body = jose.utils.base64url_decode(bytes(dialog["body"], 'utf-8'))
    f = open(wav_filename, "wb")
    f.write(decoded_body)
    f.close()

    print(vcon)

    # convert mp3 file to wav file
    sound = AudioSegment.from_wav(wav_filename)
    sound.export(mp3_filename, format="mp3")

    # Transcribe it
    dg_client = Deepgram(DEEPGRAM_KEY)
    audio = open(wav_filename, 'rb')
    source = {
      'buffer': audio,
      'mimetype': MIMETYPE
    }
    transcription = await dg_client.transcription.prerecorded(source, 
        {   'punctuate': True,
            'multichannel': False,
            'language': 'en',
            'model': 'general',
            'punctuate': True,
            'tier':'enhanced',
        })

    analysis_element = {}
    analysis_element["type"] = "transcript"
    analysis_element["dialog"] = 0
    analysis_element["body"] = transcription
    analysis_element["encoding"] = "json"
    analysis_element["vendor"] = "deepgram"
    vcon['analysis'] = []
    vcon['analysis'].append(analysis_element)
    print(transcription)

    return templates.TemplateResponse("vcon.html", {"request": request, "id": id, "vcon": vcon, "transcription": transcription})




@app.get("/vcon/{id}", response_class=JSONResponse)
async def get_vcon(id: PyObjectId, version: str = "latest"):
    if version == "latest":
        vcon = await db["vcons"].find_one({"_id": id})
    else:
        vcon = await db["vcons"].find_one({"_id": id, "version": version})
    return vcon

@app.put(
    "/vcon/{id}", response_description="Update a single vcon", response_model=VconModel
)
@app.put(
    "/vcon/{id}/{version}", response_description="Update a single vcon", response_model=VconModel
)

@app.delete(
    "/vcon/{id}", response_description="Delete a single vcon", response_model=VconModel
)
@app.delete(
    "/vcon/{id}/{version}", response_description="Delete a single vcon", response_model=VconModel
)

@app.delete("/vcon/{id}", response_description="Delete a vcon")
async def delete_vcon(id: str):
    delete_result = await db["vcons"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Vcon {id} not found")