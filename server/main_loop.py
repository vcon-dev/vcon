import importlib
from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
import redis_mgr
from redis_mgr import set_key, get_key
from settings import TICK_INTERVAL
from rocketry import Rocketry

logger = init_logger(__name__)

scheduler_app = Rocketry(execution="async")

if TICK_INTERVAL > 0:
    @scheduler_app.task(f"every {TICK_INTERVAL} seconds")  
    async def run_tick():
        await tick()

app = FastAPI.conserver_app
app.scheduler = scheduler_app

redis_mgr.create_pool()

# We decorate this with the TICK path so that we can use external tools to trigger the tick
@app.get("/tick")
async def tick():
    logger.debug("Starting tick")
    r = redis_mgr.get_client()

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
            inbound_vcon = await r.lpop(ingress_list)
            if not inbound_vcon:
                continue

            inbound_vcon = inbound_vcon.decode('utf-8')
            logger.debug("Processing vCon %s", inbound_vcon)
            # If there is a vCon to process, process it
            for link_name in chain_details['links']:
                logger.debug("Processing link %s", link_name)
                link = await get_key(f"link:{link_name}")
                module_name = link['module']

                module = importlib.import_module(module_name)
                options = link.get('options', module.default_options)
                logger.debug("Running module %s with options %s", module_name, options)
                result = await module.run(inbound_vcon, options)
                if not result:
                    # This means that the module does not want to forward the vCon
                    logger.debug("Module %s did not want to forward the vCon, no result returned. Ending chain", module_name)
                    continue
                
                # If the module wants to forward the vCon, check if it is the last link in the chain
                if link_name == chain_details['links'][-1]:
                    # If it is, then we need to put it in the outbound queue
                    for egress_list in chain_details['egress_lists']:
                        await r.lpush(egress_list, inbound_vcon)

                    for storage_name in chain_details.get("storages", []):
                        try:
                            storage = await get_key(f"storage:{storage_name}")
                            module_name = storage['module']
                            module = importlib.import_module(module_name)
                            options = storage.get('options', module.default_options)
                            result = await module.save(inbound_vcon, options)
                        except Exception as e:
                            logger.error("Error saving vCon %s to storage %s: %s", inbound_vcon, storage, e)
    
    logger.debug("Finished processing chain %s", chain_name)


