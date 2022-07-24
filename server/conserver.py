import os
from tokenize import String
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.conserver

VCON_VERSION = "0.1.1"

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class VconModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    vcon: str
    parties: List[dict] = []
    dialog: List[dict] = []
    analysis: List[dict] = []
    attachments: List[dict] = []
    
    class Config:
        json_encoders = {ObjectId: str}


class UpdateVconModel(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    course: Optional[str]
    gpa: Optional[float]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }


@app.post("/", response_description="Add new vcon", response_model=VconModel)
async def create_vcon(vcon: VconModel = Body(...)):
    vcon = jsonable_encoder(vcon)
    new_vcon = await db["vcons"].insert_one(vcon)
    created_vcon = await db["vcons"].find_one({"_id": new_vcon.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_vcon)


@app.get(
    "/", response_description="List all vcons", response_model=List[VconModel]
)
async def list_vcons():
    vcons = await db["vcons"].find().to_list(1000)
    return vcons


@app.get(
    "/{id}", response_description="Get a single vcon", response_model=VconModel
)
async def show_vcon(id: str):
    if (vcon := await db["vcons"].find_one({"_id": ObjectId(id)})) is not None:
        return vcon

    raise HTTPException(status_code=404, detail=f"Vcon {id} not found")


@app.put("/{id}", response_description="Update a vcon", response_model=VconModel)
async def update_vcon(id: str, vcon: UpdateVconModel = Body(...)):
    vcon = {k: v for k, v in vcon.dict().items() if v is not None}

    if len(vcon) >= 1:
        update_result = await db["vcons"].update_one({"_id": id}, {"$set": vcon})

        if update_result.modified_count == 1:
            if (
                updated_vcon := await db["vcons"].find_one({"_id": id})
            ) is not None:
                return updated_vcon

    if (existing_vcon := await db["vcons"].find_one({"_id": id})) is not None:
        return existing_vcon

    raise HTTPException(status_code=404, detail=f"Vcon {id} not found")


@app.delete("/{id}", response_description="Delete a vcon")
async def delete_vcon(id: str):
    delete_result = await db["vcons"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Vcon {id} not found")