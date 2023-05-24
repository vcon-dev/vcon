# This is a version of the main.py file found in ../../../server/main.py for testing the plugin locally.
# Use the command `poetry run dev` to run this.
from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
import datetime
import redis_mgr

app = FastAPI.conserver_app
scheduler = app.scheduler
logger = init_logger(__name__)

from typing import Optional
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Body, UploadFile
from starlette.responses import FileResponse

from pydantic import BaseModel
from typing import List, Optional

class Source(str, Enum):
    email = "email"
    file = "file"
    chat = "chat"
    call = 'call'

class AnalysisType(str, Enum):
    sentiment = "sentiment"
    topic = "topic"
    entity = "entity"
    intent = "intent"
    summary = "summary"
    keywords = "keywords"
    transcript = "transcript"
    promises = "promises"
    raw = "raw"
    script="script"

class DocumentMetadata(BaseModel):
    source: Optional[Source] = None
    source_id: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[str] = None
    author: Optional[str] = None
    recording_url: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_email: Optional[str] = None
    customer_email: Optional[str] = None
    customer_telephone: Optional[str] = None
    store_name: Optional[str] = None
    analysis_type: Optional[AnalysisType] = None

class DocumentChunkMetadata(DocumentMetadata):
    document_id: Optional[str] = None
    
class DocumentChunk(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: DocumentChunkMetadata
    embedding: Optional[List[float]] = None


class DocumentChunkWithScore(DocumentChunk):
    score: float


class Document(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: Optional[DocumentMetadata] = None


class DocumentWithChunks(Document):
    chunks: List[DocumentChunk]


class DocumentMetadataFilter(BaseModel):
    source: Optional[Source] = None
    source_id: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    author: Optional[str] = None
    recording_url: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_email: Optional[str] = None
    customer_email: Optional[str] = None
    customer_telephone: Optional[str] = None
    store_name: Optional[str] = None
    analysis_type: Optional[AnalysisType] = None

class Query(BaseModel):
    query: str
    filter: Optional[DocumentMetadataFilter] = None
    top_k: Optional[int] = 3


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
    print("get_manifest")
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


@app.post("/query", response_model=QueryResponse)
async def query_main(request: QueryRequest = Body(...)):
    try:
        print("request.queries", request.queries)
        results = await datastore.query(
            request.queries,
        )
        return QueryResponse(results=results)
    except Exception as e:
        print("Error:", e)
        #  Print all the details of the exception
        import traceback
        print(traceback.format_exc())
        
        raise HTTPException(status_code=500, detail="Internal Service Error")

