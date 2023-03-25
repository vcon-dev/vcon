import importlib
from lib.logging_utils import init_logger
from fastapi.applications import FastAPI
from load_config import (
    load_config,
)
import redis_mgr

logger = init_logger(__name__)
logger.info("Conserver starting up")
app = FastAPI.conserver_app

@app.on_event("startup")
async def startup():
    logger.debug("Loading configuration")
    chain_names = await load_config()
    logger.info("Loaded chains %s", chain_names)
    app.state.chain_names = chain_names
    # We should call "start on the modudles here"



@app.get("/tick")
async def tick():
    r = await redis_mgr.get_client()
    # We should make this more dynamic

    # Get list of chains from redis
    chain_names = await r.keys("chain*")
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
                link = await r.json().get(f"link:{link_name}")
                module_name = link['module']

                module = importlib.import_module(module_name)
                options = link.get('options', module.default_options)
                logger.debug("Running module %s with options %s", module_name, options)
                result = await module.run(inbound_vcon, options)
                if not result:
                    # This means that the module does not want to forward the vCon
                    logger.debug("Module %s did not want to forward the vCon", module_name)
                    continue
                
                # If the module wants to forward the vCon, check if it is the last link in the chain
                if link_name == chain_details['links'][-1]:
                    # If it is, then we need to put it in the outbound queue
                    for egress_list in chain_details['egress_lists']:
                        await r.lpush(egress_list, inbound_vcon)
    
    logger.debug("Finished processing chain %s", chain_name)




