import importlib
import time
import redis_mgr
# from server.load_config import (
#     load_config,
# )
from lib.logging_utils import init_logger
from lib.metrics import init_metrics, stats_gauge, stats_count
from lib.error_tracking import init_error_tracker
import signal
from typing import List, TypedDict, Optional
from dlq_utils import get_ingress_list_dlq_name
from config import get_config
from storage.base import Storage

shutdown_requested = False


class ChainConfig(TypedDict):
    name: str
    links: Optional[List[str]]
    storages: Optional[List[str]]
    ingress_lists: List[str]
    egress_lists: Optional[List[str]]
    enabled: int
    timeout: Optional[int]


IngressChainMap = dict[str, ChainConfig]


config: dict | None = None


def signal_handler(signum, frame):
    logger.info('SIGTERM received, initiating graceful shutdown...')
    # Set a global flag to stop the loop or exit the blocking call safely
    global shutdown_requested
    shutdown_requested = True


# Register the signal handler for SIGTERM
signal.signal(signal.SIGTERM, signal_handler)

init_error_tracker()
init_metrics()
logger = init_logger(__name__)
imported_modules = {}

# TODO - address potential reconnect issues
r = redis_mgr.get_client()


class VconChainRequest:
    vcon_id: str
    chain_details: ChainConfig

    def __init__(self, chain_details: ChainConfig, vcon_id: str):
        self.vcon_id = vcon_id
        self.chain_details = chain_details

    def process(self):
        vcon_started = time.time()
        logger.info("Started processing vCon %s", self.vcon_id)

        for link_name in self.chain_details["links"]:
            should_continue_chain = self._process_link(link_name)
            if not should_continue_chain:
                logger.info("Link %s did not want to forward vCon %s. Ending chain", link_name, self.vcon_id)
                break
        self._wrap_up()
        vcon_processing_time = round(time.time() - vcon_started, 3)
        logger.info(
            "Finsihed processing vCon %s in %s seconds",
            self.vcon_id,
            vcon_processing_time,
            extra={"vcon_processing_time": vcon_processing_time},
        )
        stats_gauge("conserver.main_loop.vcon_processing_time", vcon_processing_time)
        stats_count("conserver.main_loop.count_vcons_processed")

    def _wrap_up(self):
        # If the module wants to forward the vCon, check if it is the last link in the chain
        # If it is, then we need to put it in the outbound queue
        for egress_list in self.chain_details.get("egress_lists", []):
            r.lpush(egress_list, self.vcon_id)

        for storage_name in self.chain_details.get("storages", []):
            self._process_storage(storage_name)

        logger.info("Finished wrap_up of chain %s for vCon: %s", self.chain_details['name'], self.vcon_id)

    def _process_storage(self, storage_name):
        try:
            Storage(storage_name).save(self.vcon_id)
        except Exception as e:
            logger.error("Error saving vCon %s to storage %s: %s", self.vcon_id, storage_name, e)

    def _process_link(self, link_name):
        logger.info("Started processing link %s for vCon: %s", link_name, self.vcon_id)
        link = config["links"][link_name]

        module_name = link["module"]
        if module_name not in imported_modules:
            imported_modules[module_name] = importlib.import_module(module_name)
        module = imported_modules[module_name]
        options = link.get("options")
        logger.info(
            "Running link %s module %s for vCon: %s",
            link_name,
            module_name,
            self.vcon_id,
        )
        started = time.time()
        should_continue_chain = module.run(self.vcon_id, link_name, options)
        link_processing_time = round(time.time() - started, 3)
        logger.info(
            "Finished link %s module %s for vCon: %s in %s seconds.",
            link_name,
            module_name,
            self.vcon_id,
            round(time.time() - started, 3),
            extra={"link_processing_time": link_processing_time},
        )
        return should_continue_chain


def get_ingress_chain_map() -> IngressChainMap:
    chains = config.get("chains", {})
    ingress_details = {}
    chain_name: str
    chain_config: dict
    for chain_name, chain_config in chains.items():
        for ingress_list in chain_config.get("ingress_lists", []):
            ingress_details[ingress_list] = {"name": chain_name, **chain_config}
    return ingress_details


def main():
    logger.info("Starting main loop")
    global config
    config = get_config()
    ingress_chain_map = get_ingress_chain_map()
    all_ingress_lists = list(ingress_chain_map.keys())
    while not shutdown_requested:
        popped_item = r.blpop(all_ingress_lists, timeout=15)
        if not popped_item:
            if shutdown_requested:
                break
            continue

        ingress_list, vcon_id = popped_item
        if shutdown_requested:  # we got something from the queue but we're shutting down
            r.lpush(ingress_list, vcon_id)  # push it back into the queue so we don't lose it
            break

        log_llen(ingress_list)
        chain_details = ingress_chain_map[ingress_list]
        vcon_chain_request = VconChainRequest(chain_details, vcon_id)
        try:
            vcon_chain_request.process()
        except Exception as e:
            logger.error("Error processing vCon %s: %s. Moving it to the Dead Letter Queue.", vcon_id, e, exc_info=True)
            r.lpush(get_ingress_list_dlq_name(ingress_list), vcon_id)


# Let's defer this.  See https://trello.com/c/NXDio6D8/1249-refactor-conserver-benchmark-logs
# def log_time(func):
#     """Decorator to log the execution time of a function."""

#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         vcon_started = time.time()
#         logger.info("Started processing vCon %s", vcon_id)
#         start_time = time.time()  # Record start time
#         result = func(*args, **kwargs)  # Call the function
#         end_time = time.time()  # Record end time
#         time_taken = end_time - start_time  # Calculate the time taken
#         print(f"Function {func.__name__!r} took {time_taken:.4f} seconds to complete.")
#         return result
#     return wrapper


def log_llen(list_name: str):
    llen = r.llen(list_name)
    logger.info(
        "Ingress list %s has %s items left",
        list_name,
        llen,
        extra={"llen": llen, "ingress_list": list_name},
    )


if __name__ == "__main__":
    main()
