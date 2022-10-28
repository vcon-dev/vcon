import os
import logging
import logging.config
import boto3
import redis
import asyncio
import importlib

from fastapi.applications import FastAPI
from fastapi_utils.tasks import repeat_every
from settings import AWS_KEY_ID, AWS_SECRET_KEY

# Load FastAPI app
app = FastAPI.conserver_app

logger = logging.getLogger(__name__)
logging.config.fileConfig('./logging.conf')
logger.info('Conserver starting up')

# Setup redis
r = redis.Redis(host='localhost', port=6379, db=0)

@app.on_event("startup")
@repeat_every(seconds=1)
def check_sqs():
    sqs = boto3.resource('sqs', region_name='us-east-1', aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY)
    queue_names = r.smembers('queue_names')
    try:
        for queue_name in queue_names:
            q = queue_name.decode("utf-8") 
            queue = sqs.get_queue_by_name(QueueName=q)
            for message in queue.receive_messages():
                message.delete()
                r.rpush(q, message.body)
    except Exception as e:
        logger.info("Error: {}".format(e))


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
    for plugin in plugins:
        try:
            new_plugin = importlib.import_module("plugins."+plugin)
            background_tasks.add(asyncio.create_task(new_plugin.start(), name=plugin))
            logger.info("Plugin started: %s", plugin)
        except Exception as e:
            logger.info("Error loading plugin: %s %s", plugin, e)

    storages = os.listdir("storage")
    for storage in storages:
        try:
            new_storage = importlib.import_module("storage."+storage)
            background_tasks.add(asyncio.create_task(new_storage.start(), name=storage))
            logger.info("Storage started: %s", storage)
        except Exception as e:
            logger.info("Error loading storage: %s %s", storage, e)

    projections = os.listdir("data_projections")
    for projection in projections:
        try:
            new_projection = importlib.import_module("data_projections."+projection)
            background_tasks.add(asyncio.create_task(new_projection.start(), name=projection))
            logger.info("Projection started: %s", projection)
        except Exception as e:
            logger.info("Error loading projection: %s %s", projection, e)


@app.on_event("shutdown")
async def shutdown_background_tasks():
    logger.info("Shutting down background tasks")
    for task in background_tasks:
        task.cancel()
        await task
        logger.info("Task cancelled: %s", task)