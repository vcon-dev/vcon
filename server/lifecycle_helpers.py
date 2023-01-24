import asyncio
import copy
import importlib
import logging
import logging.config
import os

import redis_mgr
import shortuuid
from lib.process_utils import start_async_process
from lib.sqs import listen_to_sqs

logger = logging.getLogger(__name__)
logger.info("Conserver helper up")


chains = []


# optionally allow a different redis queue name for testing purposes
async def process_queue(sqs_queue_name, r, redis_queue_name=None): 
    if redis_queue_name == None:
        redis_queue_name = sqs_queue_name
    async for message in listen_to_sqs(sqs_queue_name.decode()):
        logger.info(f"Received message from the SQS {sqs_queue_name}")
        await r.rpush(redis_queue_name, message.body)
        message.delete()

async def check_sqs():
    logger.info("Starting check_sqs")
    # Don't want to create a pool every iteration, this function gets called
    # every second.
    if redis_mgr.REDIS_POOL is None:
        logger.error("redis pool not initialized in check_sqs")
        redis_mgr.create_pool()
    try:
        r = redis_mgr.get_client()
    except Exception:
        redis_mgr.create_pool()
        r = redis_mgr.get_client()

    queue_names = await r.smembers("queue_names")
    try:
        tasks = []
        for queue_name in queue_names:
            task = asyncio.create_task(process_queue(queue_name, r))
            tasks.append(task)
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Check SQS Cancelled")
    except Exception as e:
        logger.error("Check SQS Error: %s", e)
        

def load_adaptors():
    logger.info("Starting load_adaptors")
    print("Load adaptors")
    adapter_processes = []
    adapters = os.listdir("adapters")
    logger.info("Iterating adaptors")
    for adapter in adapters:
        try:
            new_adapter = importlib.import_module("adapters." + adapter)
            logger.info("Loading adaptors %s", adapter)
            process = start_async_process(new_adapter.start)
            adapter_processes.append(process)
            logger.info("Adapter started: %s", adapter)
        except Exception as e:
            logger.info("Error loading adapter: %s %s", adapter, e)
    return adapter_processes


async def update_available_blocks():
    logger.info("Starting update_available_blocks")
    redis_mgr.create_pool()
    if redis_mgr.REDIS_POOL is None:
        logger.error("redis pool not initialized in load_services")
        redis_mgr.create_pool()
    r = redis_mgr.get_client()

    available_blocks = []

    plugins = os.listdir("plugins")
    for plugin in plugins:
        available_blocks.append("plugins." + plugin)

    storages = os.listdir("storage")
    for storage in storages:
        available_blocks.append("storage." + storage)

    projections = os.listdir("data_projections")
    for projection in projections:
        available_blocks.append("data_projections." + projection)

    await r.delete("available_blocks")
    await r.sadd("available_blocks", *available_blocks)


class TransformerProcess:
    def __init__(self, name, chain_id):
        self.name = name
        self.chain_id = chain_id
        self.module = importlib.import_module(name)
        self.options = copy.deepcopy(self.module.default_options)
        self.options["egress-topics"].append(self.egress_topic())
        self.process = None

    def __str__(self):
        return self.name

    def egress_topic(self):
        return f"{self.name}_{self.chain_id}"

    def update_ingress(self, topic_name):
        self.options["ingress-topics"].append(topic_name)

    def start(self):
        self.process = start_async_process(self.module.start, self.options)

    def join(self):
        self.process.join()



class Pipeline:
    def __init__(self, nodes):
        self.pipeline_id = shortuuid.uuid()
        self.transformer_processes = []
        for node in nodes:
            transformer_process = TransformerProcess(node, self.pipeline_id)
            self.add_to_pipeline(transformer_process)

    def add_to_pipeline(self, transformer_process):
        if len(self.transformer_processes) > 0:
            last_process = self.transformer_processes[-1]
            transformer_process.update_ingress(last_process.egress_topic())
        self.transformer_processes.append(transformer_process)

    def start(self):
        for transformer_process in self.transformer_processes:
            transformer_process.start()

    def join(self):
        for transformer_process in self.transformer_processes:
            transformer_process.join()

    def __str__(self):
        return " -> ".join([transformer_process.__str__() for transformer_process in self.transformer_processes])


class TaskMonitor:
    def __init__(self):
        self._task_dict = {}
        self._check_period = 1
        self._running = None

    def stop(self):
        if self._running is not None:
            self._running.cancel()
            self._running = None

    def schedule(self):
        logger.info(
            "TaskMonitor.scheduling running: {} cancelled: {}".format(
                self._running is not None,
                "N/A" if self._running is None else self._running.cancelled(),
            )
        )
        if self._running is None or self._running.cancelled():
            loop = asyncio.get_event_loop()
            logger.info("Scheduling TaskMonitor")
            self._running = loop.call_later(self._check_period, self.check_tasks)

    def check_tasks(self):
        self.show_task_diff()

        if self._running is not None:
            self.schedule()

    def show_task_diff(self):
        tasks = asyncio.all_tasks()
        new_task_dict = {}
        for task in tasks:
            new_task_dict[task.get_name()] = task

        added_tasks = set(new_task_dict.keys()).difference(self._task_dict.keys())
        removed_tasks = set(self._task_dict.keys()).difference(new_task_dict.keys())

        tasks_changed = False

        for task_name in added_tasks:
            tasks_changed = True
            logger.info("Task {} added".format(task_name))

        for task_name in removed_tasks:
            tasks_changed = True
            logger.info("Task {} removed".format(task_name))

        if tasks_changed:
            logger.info("{} Tasks running".format(len(new_task_dict.keys())))

        self._task_dict = new_task_dict

    def show_running_tasks(self):

        for task_name in self._task_dict.keys():
            task = self._task_dict[task_name]
            logger.info("Task: {} stack: {}".format(task.get_name(), task.get_stack()))


task_monitor = TaskMonitor()
task_monitor.schedule()


async def load_pipelines():
    logger.info("Starting load_service")
    redis_mgr.create_pool()
    task_monitor.schedule()
    if redis_mgr.REDIS_POOL is None:
        logger.error("redis pool not initialized in load_services")
        redis_mgr.create_pool()
    r = redis_mgr.get_client()
    active_chains = await r.smembers("active_chains")
    logger.info("Active chains %s", active_chains)
    pipelines = []
    for chain in active_chains:
        nodes = chain.decode().split(",")
        pipeline = Pipeline(nodes)
        logger.info("Starting pipeline %s", pipeline)
        pipeline.start()
        pipelines.append(pipeline)
    return pipelines
