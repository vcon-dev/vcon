import importlib
from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
import redis_mgr
from redis_mgr import set_key, get_key
from settings import TICK_INTERVAL
from rocketry import Rocketry
from rocketry.log import MinimalRecord
from redbird.repos import CSVFileRepo

logger = init_logger(__name__)

repo = CSVFileRepo(filename="tasks.csv", model=MinimalRecord)

scheduler_app = Rocketry(execution="async", logger_repo=repo)

if TICK_INTERVAL > 0:
    tick_interval_str = f"every {TICK_INTERVAL} ms"
    logger.info("tick_interval_str: %s", tick_interval_str)

    @scheduler_app.task(tick_interval_str)
    async def run_tick():
        await tick()        

app = FastAPI.conserver_app
app.scheduler = scheduler_app

# We decorate this with the TICK path so that we can use external tools to trigger the tick
@app.get("/tick",
    status_code=204,
    summary="Makes a tick happen on the conserver. Can be used to trigger a tick from outside the conserver.",
    description="Makes a tick happen on the conserver. Can be used to trigger a tick from outside the conserver. Chains are processed on each tick.", 
    tags=["tick"])
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

        logger.debug("Checking chain %s", chain_name)
        chain_details = await r.json().get(chain_name)
        for ingress_list in chain_details['ingress_lists']:
            vcon_id = await r.lpop(ingress_list)
            if not vcon_id:
                continue

            vcon_id = vcon_id.decode('utf-8')
            logger.debug("Processing vCon %s", vcon_id)
            # If there is a vCon to process, process it
            for link_name in chain_details['links']:
                logger.debug("Processing link %s", link_name)
                link = await get_key(f"link:{link_name}")
                module_name = link['module']

                module = importlib.import_module(module_name)
                options = link.get('options')
                logger.debug("Running module %s with options %s", module_name, options)
                result = await module.run(vcon_id, options)
                if not result:
                    # This means that the module does not want to forward the vCon
                    logger.debug("Module %s did not want to forward the vCon, no result returned. Ending chain", module_name)
                    continue
                
                # If the module wants to forward the vCon, check if it is the last link in the chain
                if link_name == chain_details['links'][-1]:
                    # If it is, then we need to put it in the outbound queue
                    for egress_list in chain_details['egress_lists']:
                        await r.lpush(egress_list, vcon_id)

                    for storage_name in chain_details.get("storages", []):
                        try:
                            storage = await get_key(f"storage:{storage_name}")
                            module_name = storage['module']
                            module = importlib.import_module(module_name)
                            options = storage.get('options', module.default_options)
                            result = await module.save(vcon_id, options)
                        except Exception as e:
                            logger.error("Error saving vCon %s to storage %s: %s", vcon_id, storage_name, e)
    
        logger.debug("Finished processing chain %s", chain_name)


