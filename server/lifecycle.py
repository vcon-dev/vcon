from rocketry import Rocketry
from redis import Redis
from rq import Queue
import subprocess
from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
from load_config import (
    load_config,
)
import redis_mgr
from process_chain import process_chain
from settings import TICK_INTERVAL, EXTERNAL_WORKERS

logger = init_logger(__name__)
logger.info("Conserver starting up")
app = FastAPI.conserver_app
scheduler = FastAPI.scheduler
queue = Queue(connection=Redis())

@app.on_event("startup")
async def startup():
    logger.info("event startup")
    redis_mgr.create_pool()
    logger.debug("Loading configuration")
    chain_names = await load_config()
    logger.info("Loaded chains %s", chain_names)
    app.state.chain_names = chain_names

    if not EXTERNAL_WORKERS:
        logger.debug("Starting internal worker")
        subprocess.Popen("rq worker --with-scheduler", shell=True)
        logger.debug("Internal worker started")

@app.on_event("shutdown")
async def shutdown():
    logger.info("event shutdown")
    await redis_mgr.shutdown_pool()

# We decorate this with the TICK path so that we can use external tools to trigger the tick
@app.get("/tick")
async def tick():
    logger.debug("Starting tick")
    r = await redis_mgr.get_client()

    # Get list of chains from redis
    # These chains are setup as redis keys in the load_config module.
    # One downside here is that although the operation of the conserver
    # is dynamic (they are read every time through the loop) the
    # loop itself is more fragile than it needs to be.
    chain_names = await r.keys("chain:*")
    for chain_name in chain_names:
        chain_name = chain_name.decode('utf-8')
        job = queue.enqueue(process_chain, chain_name)
        logger.debug("Enqueued job %s", job.id)
    
if TICK_INTERVAL > 0:
    @scheduler.task(f"every {TICK_INTERVAL} seconds")  
    async def run_tick():
        await tick()        

