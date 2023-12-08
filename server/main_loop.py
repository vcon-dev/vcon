import importlib
import time
from lib.logging_utils import init_logger
import redis_mgr
from redis_mgr import get_key
from settings import TICK_INTERVAL
from rocketry import Rocketry
from rocketry.log import MinimalRecord
from redbird.repos import CSVFileRepo
from load_config import (
    load_config,
)
import asyncio
import logging
from datetime import datetime

import logging.config
from settings import LOGGING_CONFIG_FILE
import sentry_sdk
import os

sentry_sdk.init(
    os.environ.get("SENTRY_DSN"),
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
)
logging.config.fileConfig(LOGGING_CONFIG_FILE)


imported_modules = {}

logger = init_logger(__name__)


async def main():
    redis_mgr.create_pool()
    await load_config()
    repo = CSVFileRepo(filename="tasks.csv", model=MinimalRecord)

    scheduler_app = Rocketry(execution="async", logger_repo=repo)

    if TICK_INTERVAL > 0:
        tick_interval_str = f"every {TICK_INTERVAL}ms"
        logger.info("tick_interval_str: %s", tick_interval_str)

        @scheduler_app.task(tick_interval_str)
        async def run_tick():
            await tick()

        rocketry_task = asyncio.create_task(scheduler_app.serve())
        await rocketry_task
    else:
        logger.info("Rocktry ticking DISABLED!!!!!!!!!!!!!!!!!!!!!!")


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
        chain_name = chain_name.decode("utf-8")

        logger.debug("Checking chain %s", chain_name)
        chain_details = await r.json().get(chain_name)
        for ingress_list in chain_details["ingress_lists"]:
            # Get up to 10 vcons...
            vcon_id = await r.rpop(ingress_list)
            # TODO Put it in to the `in_progress_list` so we can put it back if we don't process it
            # [(vcon_uuid, timestamp), ...]
            if not vcon_id:
                continue
            llen = await r.llen(ingress_list)
            logger.info(
                "Ingress list %s has %s items left",
                ingress_list,
                llen,
                extra={"llen": llen, "ingress_list": ingress_list},
            )

            vcon_id = vcon_id.decode("utf-8")
            vcon_started = time.time()
            logger.info("Started processing vCon %s", vcon_id)
            # If there is a vCon to process, process it
            for link_name in chain_details["links"]:
                logger.info(
                    "Started processing link %s for vCon: %s", link_name, vcon_id
                )
                link = await get_key(f"link:{link_name}")
                module_name = link["module"]
                if module_name not in imported_modules:
                    imported_modules[module_name] = importlib.import_module(module_name)
                module = imported_modules[module_name]
                options = link.get("options")
                logger.info(
                    "Running link %s module %s for vCon: %s",
                    link_name,
                    module_name,
                    vcon_id,
                )
                started = time.time()
                result = await module.run(vcon_id, options)
                link_processing_time = round(time.time() - started, 3)
                logger.info(
                    "Finished link %s module %s for vCon: %s in %s seconds.",
                    link_name,
                    module_name,
                    vcon_id,
                    round(time.time() - started, 3),
                    extra={"link_processing_time": link_processing_time},
                )
                if not result:
                    # This means that the module does not want to forward the vCon
                    logger.info(
                        "Module %s did not want to forward the vCon %s, no result returned. Ending chain",
                        module_name,
                        vcon_id,
                    )
                    continue

                # If the module wants to forward the vCon, check if it is the last link in the chain
                if link_name == chain_details["links"][-1]:
                    # If it is, then we need to put it in the outbound queue
                    for egress_list in chain_details["egress_lists"]:
                        await r.lpush(egress_list, vcon_id)

                    for storage_name in chain_details.get("storages", []):
                        try:
                            storage = await get_key(f"storage:{storage_name}")
                            module_name = storage["module"]

                            if module_name not in imported_modules:
                                imported_modules[module_name] = importlib.import_module(
                                    module_name
                                )
                            module = imported_modules[module_name]

                            options = storage.get("options", module.default_options)
                            logger.info(
                                "Running storage %s module %s for vCon: %s",
                                storage_name,
                                module_name,
                                vcon_id,
                            )
                            started = time.time()
                            result = await module.save(vcon_id, options)
                            storage_processing_time = round(time.time() - started, 3)
                            logger.info(
                                "Finished storage %s module %s for vCon: %s in %s seconds.",
                                storage_name,
                                module_name,
                                vcon_id,
                                storage_processing_time,
                                extra={
                                    "storage_processing_time": storage_processing_time
                                },
                            )
                        except Exception as e:
                            logger.error(
                                "Error saving vCon %s to storage %s: %s",
                                vcon_id,
                                storage_name,
                                e,
                            )
                logger.info(
                    "Finished processing link %s for vCon: %s", link_name, vcon_id
                )

            vcon_processing_time = round(time.time() - vcon_started, 3)
            logger.info(
                "Finsihed processing vCon %s in %s seconds",
                vcon_id,
                vcon_processing_time,
                extra={"vcon_processing_time": vcon_processing_time},
            )
            enqueued_time_bytes = await r.get(f"vcon_enqueued:{vcon_id}")
            if enqueued_time_bytes is not None:
                enqueued_time = enqueued_time_bytes.decode("utf-8")
                processing_ended_time = datetime.now()
                time_diff = processing_ended_time - datetime.strptime(
                    enqueued_time, "%y/%m/%d, %H:%M:%S"
                )
                logger.info(
                    "vcon %s took %s seconds to appear in call log",
                    vcon_id,
                    time_diff.seconds,
                    extra={"seconds": time_diff.seconds},
                )

            # TODO Remove vcon from `in_progress_list` so we know it is done
            # TODO Add new task which move vcon from `in_progress_list` to `ingress_list` if it is there for too long

        logger.debug("Finished processing chain %s", chain_name)


if __name__ == "__main__":
    asyncio.run(main())
