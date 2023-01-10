import asyncio
from time import sleep
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
from settings import AWS_KEY_ID, AWS_SECRET_KEY, REDIS_URL, LOG_LIMIT


chains = []

# Load FastAPI app
app = FastAPI.conserver_app
logger = logging.getLogger(__name__)
logger.info('Conserver starting up')

# Setup redis
r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)


# Periodically check for new data to extract
@app.on_event("startup")
@repeat_every(seconds=1)
async def check_sqs():
    sqs = boto3.resource('sqs', region_name='us-east-1', aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY)
    queue_names = await r.smembers('queue_names')
    try:
        for queue_name in queue_names:
            process_messages = True
            while process_messages:
                sleep(0.1)
                process_messages = False
                queue = sqs.get_queue_by_name(QueueName=queue_name)
                for message in queue.receive_messages(MaxNumberOfMessages=10):
                    logger.info("Received message from the SQS")
                    process_messages = True
                    message.delete()
                    await r.rpush(queue_name, message.body)
    except Exception as e:
        logger.info("Error: {}".format(e))




class Transformer:

    def __init__(self, name, chain_id):
        self.name = name
        self.chain_id = chain_id
        self.module = importlib.import_module(name)
        self.options = self.module.default_options
        self.options['egress-topics'].append(self.default_egress_topic())
        self.task = None

    def __str__(self):
        return self.name

    def default_egress_topic(self):
        return f"{self.name}_{self.chain_id}"

    def append(self, transformer):
        transformer.options['ingress-topics'].append(self.default_egress_topic())


    def start(self):
        self.task = asyncio.create_task(self.module.start(self.options))

    async def cancel(self):
        self.task.cancel()
        await self.task

    


class Pipeline:

    def __init__(self, chain):
        self.pipeline_id = shortuuid.uuid()
        self.pipeline_tasks = []
        for node in chain:
            transformer = Transformer(node, self.pipeline_id)
            self.add_to_pipeline(transformer)

    def add_to_pipeline(self, transformer):
        if len(self.pipeline_tasks) > 0:
            self.pipeline_tasks[-1].append(transformer)
        self.pipeline_tasks.append(transformer)

    def start(self):
        for task in self.pipeline_tasks:
            task.start();

    async def cancel(self):
        for task in self.pipeline_tasks:
            await task.cancel();
    
    def __str__(self):
        return " -> ".join([task.__str__() for task in self.pipeline_tasks])

async def configure_and_start_pipeline(chain):
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
    pipline = Pipeline(chain)
    pipline.start()
    background_tasks.add(pipline)

    logger.info("Pipeline tasks: {}".format(pipline))


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
        chain = chain.split(",")
        logger.info("Chain: {}".format(chain))
        asyncio.create_task(configure_and_start_pipeline(chain))

async def observe():
    logger.info("Observer started")
    while True:
        try:
            p = r.pubsub(ignore_subscribe_messages=True)
            await p.subscribe('ingress-vcons')
            async for message in p.listen():
                await process_vcon_message(message);
        except asyncio.CancelledError:
            logger.info("observer Cancelled")
            break
        except Exception:
            continue
    logger.info("Observer stopped")


    


async def process_vcon_message(message):
    logger.debug("Got message %s", message)
    vConUuid = message['data']
    await r.lpush('call_log_list', vConUuid)
    await r.ltrim('call_log_list', 0, LOG_LIMIT)
    


@app.on_event("startup")
async def start_observer():
    logger.info("Starting observer")
    task = asyncio.create_task(observe())
    background_tasks.add(task)



@app.on_event("shutdown")
async def shutdown_background_tasks():
    logger.info("Shutting down background tasks")
    for task in background_tasks:
        await task.cancel()
        logger.info("Task cancelled: %s", task)
