import os
import json
import redis_mgr
from redis_mgr import get_key, set_key
import importlib
import yaml
from lib.logging_utils import init_logger

logger = init_logger(__name__)

# Load the environment
config_file = os.getenv("CONSERVER_CONFIG_FILE", "./example_config.yml")
update_config_file = os.getenv("UPDATE_CONFIG_FILE")

async def load_config():
    logger.info("Loading config")
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
    except OSError as e:
        logger.error(f"Cannot find config file {config_file}")
        return 
    
    # Get the redis client
    r = await redis_mgr.get_client()

    # Set the links
    logger.debug("Configuring the links")
    for link_name in config.get("links",[]):
        link = config['links'][link_name]
        await set_key(f"link:{link_name}", link)
        logger.debug(f"Added link {link_name}")

    # Set the storage destinations
    logger.debug("Configuring the storage destinations")
    for storage_name in config.get("storages", []):
        storage = config['storages'][storage_name]
        await set_key(f"storage:{storage_name}", storage)
        logger.debug(f"Added storage {storage_name}")

    # Set the chains
    logger.debug("Deleting old chains")
    chain_names = await r.keys("chain*")
    for chain_name in chain_names:
        await r.delete(chain_name)
        
    logger.debug("Configuring the chains")
    chain_names = []
    for chain_name in config.get('chains', []):
        chain = config['chains'][chain_name]
        await set_key(f"chain:{chain_name}", chain)
        logger.debug(f"Added chain {chain_name}")
        chain_names.append(chain_name)
    
    # Now that system is loaded up, start whatever adapters there are.
    logger.debug("Starting the adapters")
    for adapter_name in config.get('adapters', []):
        adapter = config['adapters'][adapter_name]
        module_name = adapter['module']
        importlib.import_module(module_name)

    logger.debug("Configuration loaded")
    return chain_names

