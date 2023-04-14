from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
from load_config import (
    load_config,
)
import redis_mgr

logger = init_logger(__name__)
logger.info("Conserver starting up")
app = FastAPI.conserver_app

@app.on_event("startup")
async def startup():
    logger.info("event startup")
    redis_mgr.create_pool()
    logger.debug("Loading configuration")
    chain_names = await load_config()
    logger.info("Loaded chains %s", chain_names)
    app.state.chain_names = chain_names


@app.on_event("shutdown")
async def shutdown():
    logger.info("event shutdown")
    await redis_mgr.shutdown_pool()

