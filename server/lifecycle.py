import asyncio
import os
import logging
import logging.config
import boto3
import redis.asyncio as redis
from redis.commands.json.path import Path
import importlib
import shortuuid

from fastapi.applications import FastAPI
from fastapi_utils.tasks import repeat_every
from settings import AWS_KEY_ID, AWS_SECRET_KEY, REDIS_URL


chains = []

# Load FastAPI app
app = FastAPI.conserver_app
logger = logging.getLogger(__name__)
logging.config.fileConfig('./logging.conf')
logger.info('Conserver starting up')

# Setup redis
r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

@app.on_event("startup")
@repeat_every(seconds=1)
async def check_sqs():
    print("Tick")

class Transformer: 
    def __init__(self, name, chain_id): 
        self.name = name 
        self.module = importlib.import_module(name)
        self.options = self.module.default_options
        self.chain_id = chain_id

    def __str__(self): 
        return self.name

    def default_egress_topic(self):
        return "{}_{}".format(self.name, self.chain_id)


async def configure_and_start_pipeline(pipeline):
    """ This function takes a string of transformations and starts them up as a pipeline

    This function gets a string that corresponds to a list of transformations 
    like "plugins.call_log,plugins.redaction".  Every transformation takes the same
    input - a vCon, and then optionally outputs a vCon. Although configurable, 
    the default input to the chain comes from the "ingress_vcon" REDIS PUB/SUB. 
    The output of one transformation is the input of the next, again using REDIS PUB/SUB.
    Each chain has a unique ID to identify it, and that UUID is the suffix of the 
    REDIS PUB/SUB channels.  The default output of the chain is the "egress_vcon".

    A transformation can act like a filter by not pushing a vCon into the egress
    channel.  This is useful for things like redaction, where you want to filter
    out certain vCons, but not others.  The transformation can also modify the
    vCon in place (typically), or create a new vCon and push that into the egress channel.

    Once the pipeline is setup, no other admin is necessary. Each transformer 
    executes on each inbound vCon.
    """
    # 
    # in order. The first 
    pipeline_id = shortuuid.uuid()
    pipeline_tasks = []
    last_egress_key = None
    for step in pipeline:
        """ For each transformer in the pipeline, import the named module. 
            Then, check to see if there's an existing options block for it.
            If not, create a new one and attach it.  Then, start the task. 
        """
        thisStep = Transformer(step, pipeline_id)
        block_egress = thisStep.default_egress_topic()
        thisStep.options['egress-topics'].append(block_egress)
        if last_egress_key:
            """If this is not the first step in the pipeline, remember to update
            the last egress key so we know what to hook the next transformer into.
            Afterwards, update the last_ingress_key for next time.
            """
            thisStep.options['ingress-topics'].append(last_egress_key)
            last_egress_key = block_egress

        # Start the plugin, add it to the list of tasks
        # and add this task to the chain of tasks.
        task = asyncio.create_task(thisStep.start(step.options))
        background_tasks.add(task)
        pipeline_tasks.append(task)
        logger.info("Starting pipeline task: {}".format(step))

    logger.info("Pipeline tasks: {}".format(pipeline_tasks))


background_tasks = set()

@app.on_event("startup")
async def load_services():
    adapters = os.listdir("adapters")
    for adapter in adapters:
        try:
            new_adapter = importlib.import_module("adapters."+adapter)
            background_tasks.add(asyncio.create_task(new_adapter.start(), name=adapter))
            logger.info("Adapter started: %s", adapter)
        except Exception as e:
            logger.info("Error loading adapter: %s %s", adapter, e)

    plugins = os.listdir("plugins")
    available_blocks = []
    for plugin in plugins:
        available_blocks.append("plugins."+plugin)

    storages = os.listdir("storage")
    for storage in storages:
        available_blocks.append("storage."+storage)

    projections = os.listdir("data_projections")
    for projection in projections:
        available_blocks.append("data_projections."+projection)

    await r.delete('available_blocks')
    await r.sadd('available_blocks', *available_blocks)

    active_chains = await r.smembers('active_chains')
    for chain in active_chains:
        chain = chain.decode("utf-8")
        chain = chain.split(",")
        logger.info("Chain: {}".format(chain))
        asyncio.create_task(configure_and_start_pipeline(chain))


@app.on_event("shutdown")
async def shutdown_background_tasks():
    logger.info("Shutting down background tasks")
    for task in background_tasks:
        task.cancel()
        await task
        logger.info("Task cancelled: %s", task)