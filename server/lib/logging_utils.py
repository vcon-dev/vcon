import logging
from settings import LOGGING_CONFIG_FILE
import logging.config

logging.config.fileConfig(LOGGING_CONFIG_FILE)


def init_logger(name):
    return logging.getLogger(name)
