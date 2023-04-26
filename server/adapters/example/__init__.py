from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
import redis_mgr

app = FastAPI.conserver_app
scheduler = app.scheduler
logger = init_logger(__name__)

"""
Entry point for the adapter.
"""
def __init__(config):
    _config = config
    logger.info(f"Starting adapater with {config}")


TICK_INTERVAL = 0
if TICK_INTERVAL > 0:
    @scheduler.task(f"every {TICK_INTERVAL} seconds")  
    async def check_for_new_events():
        logger.info("TICK!")    

# We decorate this with the TICK path so that we can use external tools to trigger the tick
@app.get("/incoming_something")
async def incoming_something_handler():
    logger.debug("Incoming Something")
    r = await redis_mgr.get_client()

