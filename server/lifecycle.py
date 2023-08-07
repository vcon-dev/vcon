from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
from load_config import (
    load_config,
)
import redis_mgr
import os
import yaml

logger = init_logger(__name__)
logger.info("Conserver starting up")
app = FastAPI.conserver_app

@app.on_event("startup")
async def startup():
    logger.info("event startup")
    redis_mgr.create_pool()
    logger.debug("Loading configuration")

    # Load the configuration from the config file
    # Load the environment
    config_file = os.getenv("CONSERVER_CONFIG_FILE", None)
    if config_file:
        logger.info("Using config file %s", config_file)
        try:
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)
        except OSError as e:
            logger.error(f"Cannot find config file {config_file}")
            return 

        chain_names = await load_config(config)
        logger.info("Loaded chains %s", chain_names)


@app.on_event("shutdown")
async def shutdown():
    logger.info("event shutdown")
    await redis_mgr.shutdown_pool()

