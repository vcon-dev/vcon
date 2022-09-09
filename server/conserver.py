
import os
import sys
import logging
from typing import Optional, List
import json
import urllib.request
from urllib.error import HTTPError
import datetime

import asyncio
import boto3

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


import settings

# Our local modules``
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
MIMETYPE="audio/wav"

# Home page route

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    vcons = await db["vcons"].find().sort("created_at",-1 ).to_list(100)
    return templates.TemplateResponse("index.html", {"request": request, "vCons": vcons})

# Conversation Route
@app.get("/conversations/{page}", response_class=HTMLResponse)
async def conversations(request: Request, page: int):
    # Paginate the vCons
    length = 12
    vcons = await db["vcons"].find().sort("created_at",-1 ).skip(page*length).limit(length).to_list(length)
    return templates.TemplateResponse("conversations.html", {"request": request, "vCons": vcons, "page": page, "length": length})


# This is the endpoint for the vcon creation that comes from
# the SNS topic
@app.post("/vcon", response_class=HTMLResponse)
async def post_vcon(request: Request):
    ingress_msg = await request.json()
    ingress_vcon = json.loads(ingress_msg["Message"])

    # Construct empty vCon, set meta data
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

    try:
        # Download the recording
        print("Downloading recording from: ", recording_url)
        recording_bytes = urllib.request.urlopen(recording_url).read()
        vCon.add_dialog_inline_recording(
        recording_bytes,
        ingress_vcon["payload"]["cdr"]["starttime"],
        ingress_vcon["payload"]["cdr"]["duration"],
        [0, 1], # parties recorded
        "audio/x-wav", # MIME type
        recording_filename)
        print("Recording downloaded")

    except urllib.error.HTTPError as err:
        error_msg = "Error retrieving recording from " + recording_url
        error_type = "HTTPError"
        error_time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        vCon.attachments.append({"error_msg": error_msg, "error_type": error_type, "error_time": error_time})

    # Save the original RingPlan JSON in the vCon
    vCon.attachments.append(ingress_vcon)


    # Save the vCon to the database
    json_string = vCon.dumps()
    vcon_dict = json.loads(json_string)
    insert_one_result = await db["vcons"].insert_one(vcon_dict)

    print("Saving to S3")
    # Save the vCon to S3
    s3 = boto3.resource(
    's3',
    region_name='us-east-1',
    aws_access_key_id=AWS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY
    )
    s3.Bucket(AWS_BUCKET).put_object(Key=str(insert_one_result.inserted_id), Body=json_string)
    print("Saved to S3")

    return JSONResponse(status_code=status.HTTP_200_OK)

@app.get(
    "/vcon/{id}", response_description="Computer Readable vCon", response_model=VconModel
)
async def show_vcon(request: Request, id: PyObjectId):
    vcon = await db["vcons"].find_one({"_id": id})
    return vcon  

@app.get("/details/{id}", response_class=HTMLResponse)
async def show_vcon(request: Request, id: str):
    print("Hello!")
    vcon = await db["vcons"].find_one({"_id": id})
    if vcon is None:
        raise HTTPException(status_code=404, detail=f"Vcon {id} not found")

        
    for index, dialog in enumerate(vcon['dialog']): 
        wav_filename = "static/{}_{}.wav".format(id, index)
        mp3_filename = "static/{}_{}.mp3".format(id, index)
        ogg_filename = "static/{}_{}.ogg".format(id, index)
        unknown_filename = "static/{}_{}".format(id, index)
        decoded_body = jose.utils.base64url_decode(bytes(dialog["body"], 'utf-8'))
        f = open(unknown_filename, "wb")
        f.write(decoded_body)
        f.close()
        # convert mp3 file to wav file
        sound = AudioSegment.from_file(unknown_filename)
        sound.export(mp3_filename, format="mp3")
        sound.export(wav_filename, format="wav")
        sound.export(ogg_filename, format="ogg")

        # Check to see if we have a transcript, create one if not
        need_transcript = True
        for analysis in vcon['analysis']:
            if analysis['type'] == 'transcript':
                need_transcript = False
                break
        if need_transcript:
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
            analysis_element["dialog"] = index
            analysis_element["body"] = transcription
            analysis_element["encoding"] = "json"
            analysis_element["vendor"] = "deepgram"
            vcon['analysis'] = []
            vcon['analysis'].append(analysis_element)
            await db["vcons"].update_one({"_id": id}, {"$push": { 'analysis': analysis_element}})

            # Update S3
            print("Transcription complete")
        else:
            print("Transcription already exists")

    return templates.TemplateResponse("vcon.html", {"request": request, "vcon": vcon})




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

