import os
import json
import redis_mgr
from lib.logging_utils import init_logger

logger = init_logger(__name__)
logger.info("Conserver starting up")

# Load the environment
config_file = os.getenv("CONSERVER_CONFIG_FILE", "./wip_config.json")
update_config_file = os.getenv("UPDATE_CONFIG_FILE")

async def load_config():
    try:
        with open(config_file, 'rb') as file_handle:
            config_file_bytes = file_handle.read()
    except OSError as e:
        logger.error(f"Cannot find config file {config_file}")
        return 
    
    config = json.loads(config_file_bytes)

    # Get the redis client
    r = await redis_mgr.get_client()

    # Set the links
    logger.debug("Configuring the links")
    for link_name in config['links']:
        link = config['links'][link_name]
        await r.json().set(f"link:{link_name}", "$", link)
        logger.debug(f"Added link {link_name}")

    # Set the storage destinations
    logger.debug("Configuring the storage destinations")
    for storage_name in config['storage']:
        storage = config['storage'][storage_name]
        await r.json().set(f"storage:{storage_name}", "$", storage)
        logger.debug(f"Added storage {storage_name}")

    # Set the chains
    logger.debug("Deleting old chains")
    chain_names = await r.keys("chain*")
    for chain_name in chain_names:
        await r.delete(chain_name)
        
    logger.debug("Configuring the chains")
    chain_names = []
    for chain_name in config['chains']:
        chain = config['chains'][chain_name]
        await r.json().set(f"chain:{chain_name}", "$", chain)
        logger.debug(f"Added chain {chain_name}")
        chain_names.append(chain_name)
    
    logger.debug("Configuration loaded")
    return chain_names

