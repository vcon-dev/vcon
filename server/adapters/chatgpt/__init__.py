# This is a version of the main.py file found in ../../../server/main.py for testing the plugin locally.
# Use the command `poetry run dev` to run this.
from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import weaviate
import os
import logging
from settings import WEVIATE_HOST, WEVIATE_API_KEY
from fastapi import Depends
import openai
from starlette.responses import FileResponse


app = FastAPI.conserver_app
scheduler = app.scheduler
logger = init_logger(__name__)


    
class DocumentChunk(BaseModel):
    vcon_id: str
    vcon_summary: str
    embedding: Optional[List[float]] = None

class DocumentChunkWithScore(DocumentChunk):
    score: float

class Document(BaseModel):
    vcon_id: str
    vcon_summary: str

class DocumentWithChunks(Document):
    chunks: List[DocumentChunk]


class Query(BaseModel):
    query: str


class QueryWithEmbedding(Query):
    embedding: List[float]


class QueryResult(BaseModel):
    query: str
    results: List[DocumentChunkWithScore]

class QueryRequest(BaseModel):
    queries: List[Query]


class QueryResponse(BaseModel):
    results: List[QueryResult]


@app.route("/.well-known/ai-plugin.json")
async def get_manifest(request):
    file_path = "./adapters/chatgpt/ai-plugin.json"
    return FileResponse(file_path, media_type="text/json")


@app.route("/.well-known/logo.png")
async def get_logo(request):
    print("get_logo")
    file_path = "./adapters/chatgpt/logo.png"
    return FileResponse(file_path, media_type="text/json")


@app.route("/.well-known/openapi.yaml")
async def get_openapi(request):
    print("get_openapi")
    file_path = "./adapters/chatgpt/openapi.yaml"
    return FileResponse(file_path, media_type="text/json")


INDEX_NAME = 'Vcon'

SCHEMA = {
    "class": INDEX_NAME
}

def get_embedding(text):
    """
    Get the embedding for a given text
    """
    results = openai.Embedding.create(input=text, model="text-embedding-ada-002")

    return results["data"][0]["embedding"]


def get_client():
    """
    Get a client to the Weaviate server
    """
    return weaviate.Client(WEVIATE_HOST,
                           auth_client_secret=weaviate.AuthApiKey(api_key=WEVIATE_API_KEY))


def init_db():
    """
    Create the schema for the database if it doesn't exist yet
    """
    client = get_client()

    if not client.schema.contains(SCHEMA):
        logging.debug("Creating schema")
        client.schema.create_class(SCHEMA)
    else:
        class_name = SCHEMA["class"]
        logging.debug(f"Schema for {class_name} already exists")
        logging.debug("Skipping schema creation")


@app.post("/query", response_model=List[QueryResult])
def query(query: Query, client=Depends(get_client)) -> List[Document]:
    """
    Query for conversations by time, agent, customer, transcript.
    Examples: "test.agent@strolid", +15083640000, "Jack Black Ford"
    """
    query_vector = get_embedding(query.query)

    results = (
        client.query.get(INDEX_NAME, ["vcon_id", "vcon_summary"])
        .with_near_vector({"vector": query_vector})
        .with_limit(4)
        .with_additional("certainty")
        .do()
    )

    docs = results["data"]["Get"][INDEX_NAME]

    return [
        QueryResult(
            query=query.query,
            results=[
                DocumentChunkWithScore(
                    vcon_id=doc["vcon_id"],
                    vcon_summary=doc["vcon_summary"],
                    score=doc["_additional"]["certainty"],
                )
                for doc in docs
            ],
        )
    ]