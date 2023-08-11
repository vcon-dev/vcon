import os
import json
import redis_mgr
from redis_mgr import get_key, set_key
import importlib
import yaml
from lib.logging_utils import init_logger
import time

logger = init_logger(__name__)
logger.debug("Loading the environment")

update_config_file = os.getenv("UPDATE_CONFIG_FILE", None)

async def load_config(config, update_config_file=update_config_file):
    # For this function, there are two approaches: to replace
    # the configuration file, or to take this configuration file
    # and overlay it. The overlay approach is the default

    # Get the redis client
    r = await redis_mgr.get_client()

    # Save the old config file in redis, so that it can be retrieved later
    logger.debug("Saving the old config")
    old_config = await get_key("config")
    if old_config:
        # Name the old config file with a unix timestamp
        ts = int(time.time())
        await set_key(f"config:{ts}", old_config)
        logger.debug("Saved the old config as config:{}".format(ts))

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

    logger.debug("Configuring the chains")
    chain_names = []
    for chain_name in config.get('chains', []):
        chain = config['chains'][chain_name]
        await set_key(f"chain:{chain_name}", chain)
        logger.debug(f"Added chain {chain_name}")
        chain_names.append(chain_name)
    
    # Now that system is xded up, start whatever adapters there are.
    logger.debug("Starting the adapters")
    for adapter_name in config.get('adapters', []):
        adapter = config['adapters'][adapter_name]
        module_name = adapter['module']
        importlib.import_module(module_name)

    # If we are updating the config file, then derive it from the database
    if update_config_file:
        logger.debug("Updating the config file")
        config = {}
        config['links'] = {}
        config['storages'] = {}
        config['chains'] = {}
        config['adapters'] = {}
        config['links'] = await r.hgetall("link:*")
        config['storages'] = await r.hgetall("storage:*")
        config['chains'] = await r.hgetall("chain:*")
        config['adapters'] = await r.hgetall("adapter:*")

        # Convert the config to yaml
        config = yaml.dump(config)

        # Write the config to the config file
        with open(update_config_file, "w") as f:
            f.write(config)

        # Save the config file in redis, so that it can be retrieved later
        logger.debug("Saving the config file")
        await set_key("config", config)

    logger.debug("Configuration loaded")
    return chain_names

