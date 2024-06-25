import os
import redis_mgr
from redis_mgr import get_key, set_key
import importlib
import yaml
from lib.logging_utils import init_logger
import time

logger = init_logger(__name__)

config_file = os.getenv("CONSERVER_CONFIG_FILE", "./example_config.yml")
update_config_file = os.getenv("UPDATE_CONFIG_FILE")


def load_config() -> list[str]:
    logger.info("Loading config")
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
    except OSError:
        logger.error(f"Cannot find config file {config_file}")
        return 
    
    # Get the redis client
    r = redis_mgr.get_client()

    # Save the old config file in redis, so that it can be retrieved later
    logger.debug("Saving the old config")
    old_config = get_key("config")
    if old_config:
        # Name the old config file with a unix timestamp
        ts = int(time.time())
        set_key(f"config:{ts}", old_config)
        logger.debug("Saved the old config as config:{}".format(ts))

    # Set the links
    logger.debug("Configuring the links")
    for link_name in config.get("links", {}):
        link = config['links'][link_name]
        set_key(f"link:{link_name}", link)
        logger.debug(f"Added link {link_name}")

    # Set the storage destinations
    logger.debug("Configuring the storage destinations")
    for storage_name in config.get("storages", {}):
        storage = config['storages'][storage_name]
        set_key(f"storage:{storage_name}", storage)
        logger.debug(f"Added storage {storage_name}")

    logger.debug("Configuring the chains")
    chain_names = []
    for chain_name in config.get('chains', {}):
        chain = config['chains'][chain_name]
        set_key(f"chain:{chain_name}", chain)
        logger.debug(f"Added chain {chain_name}")
        chain_names.append(chain_name)
    
    # If we are updating the config file, then derive it from the database
    if update_config_file:
        logger.debug("Updating the config file")
        config = {}
        config['links'] = {}
        config['storages'] = {}
        config['chains'] = {}
        config['links'] = r.hgetall("link:*")
        config['storages'] = r.hgetall("storage:*")
        config['chains'] = r.hgetall("chain:*")

        # Convert the config to yaml
        config = yaml.dump(config)

        # Write the config to the config file
        with open(update_config_file, "w") as f:
            f.write(config)

    # Save the config file in redis, so that it can be retrieved later
    logger.debug("Saving the config file")
    set_key("config", config)

    logger.debug("Configuration loaded")
    return chain_names

