import importlib
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

import logging.config
from settings import LOGGING_CONFIG_FILE

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
            vcon_id = await r.lpop(ingress_list)
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
                logger.info("Running module %s for vCon: %s", module_name, vcon_id)
                result = await module.run(vcon_id, options)
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
                            result = await module.save(vcon_id, options)
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
        logger.debug("Finished processing chain %s", chain_name)


if __name__ == "__main__":
    asyncio.run(main())
