import importlib
import time
import redis_mgr
from server.load_config import (
    load_config,
)
from lib.logging_utils import init_logger
from lib.metrics import init_metrics, stats_gauge, stats_count
from lib.error_tracking import init_error_tracker
import json
from settings import GLOBAL_INGRESS
from pydantic import BaseModel
import signal
from typing import Optional

shutdown_requested = False


def signal_handler(signum, frame):
    print('SIGTERM received, initiating graceful shutdown...')
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


class VconChainRequest(BaseModel):
    chain_name: str
    vcon_id: str
    chain_details: Optional[dict] = None

    @classmethod
    def validate_and_construct(cls, vcon_chain_request_str):
        _vcon_chain_request = cls.model_validate_json(vcon_chain_request_str)
        _vcon_chain_request.chain_details = r.json().get(f"chain:{_vcon_chain_request.chain_name}")
        return _vcon_chain_request

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
        for egress_chain_name in self.chain_details.get("egress_chains", []):
            data = {"vcon_id": self.vcon_id, "chain_name": egress_chain_name}
            data_str = json.dumps(data)
            r.lpush(GLOBAL_INGRESS, data_str)

        for storage_name in self.chain_details.get("storages", []):
            self._process_storage(storage_name)

        logger.info("Finished wrap_up of chain %s for vCon: %s", self.chain_name, self.vcon_id)

    def _process_storage(self, storage_name):
        try:
            storage_key = f"storage:{storage_name}"
            storage = r.json().get(storage_key)
            module_name = storage["module"]

            if module_name not in imported_modules:
                imported_modules[module_name] = importlib.import_module(module_name)
            module = imported_modules[module_name]

            options = storage.get("options", module.default_options)
            logger.info("Running storage %s module %s for vCon: %s", storage_name, module_name, self.vcon_id)
            started = time.time()
            module.save(self.vcon_id, options)
            storage_processing_time = round(time.time() - started, 3)
            logger.info(
                "Finished storage %s module %s for vCon: %s in %s seconds.",
                storage_name,
                module_name,
                self.vcon_id,
                storage_processing_time,
                extra={"storage_processing_time": storage_processing_time},
            )
        except Exception as e:
            logger.error("Error saving vCon %s to storage %s: %s", self.vcon_id, storage_name, e)

    def _process_link(self, link_name):
        logger.info("Started processing link %s for vCon: %s", link_name, self.vcon_id)
        link_key = f"link:{link_name}"
        link = r.json().get(link_key)
        #link = json.loads(link_str)

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


def main():
    load_config()
    while not shutdown_requested:
        poped_item = r.blpop(GLOBAL_INGRESS, timeout=15)
        if shutdown_requested:
            if poped_item:
                r.lpush(GLOBAL_INGRESS, poped_item[1])  # push it back into the list since we're shutting down
            break
        if not poped_item:  # it was a timeout
            continue
        log_llen()
        vcon_chain_request_str = poped_item[1]
        print(f"Type of vcon_chain_request_str: {type(vcon_chain_request_str)}")
        print(f"Processing vcon_chain_request_str: {vcon_chain_request_str}")
        vcon_chain_request = VconChainRequest.validate_and_construct(vcon_chain_request_str)
        vcon_chain_request.process()


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


def log_llen():
    llen = r.llen(GLOBAL_INGRESS)
    logger.info(
        "Ingress list %s has %s items left",
        GLOBAL_INGRESS,
        llen,
        extra={"llen": llen, "ingress_list": GLOBAL_INGRESS},
    )


if __name__ == "__main__":
    main()
