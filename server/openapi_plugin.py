from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
from fastapi import APIRouter
import redis_mgr
from api_models import Vcon, Analysis
from fastapi_pagination import Page, paginate
import os
import json
from fastapi.openapi.utils import get_openapi

logger = init_logger(__name__)
app = FastAPI.conserver_app
router = APIRouter()

@app.get('/.well-known/ai-plugin.json')
def serve_manifest():
    # Read the file and return it
    f = open(os.path.join(os.path.dirname(__file__), 'ai-plugin.json'), 'r')
    json_data = f.read()
    f.close()
    return json.loads(json_data)


@router.get("/calls/{since}", response_model=Page[str])
async def get_calls(since: str):
    r = redis_mgr.get_client()
    keys = await r.keys("vcon:*")
    uuids = [key.replace("vcon:", "") for key in keys]
    return paginate(uuids)


@router.get("/openapi.json")
async def openapi():
    chat_gpt_openapi_schema = get_openapi(
        title="Custom title",
        version="0.0.2",
        description="An OpenAPI schema for ChatGPT",
        routes=router.routes,
    )
    chat_gpt_openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    return chat_gpt_openapi_schema

app.include_router(
    router,
    prefix="/chatgpt",
    tags=["chatgpt"]
)




