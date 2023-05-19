import logging
import logging.config
from settings import LOGGING_CONFIG_FILE

logging.config.fileConfig(LOGGING_CONFIG_FILE)


def init_logger(name):
    return logging.getLogger(name)
