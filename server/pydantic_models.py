from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


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
