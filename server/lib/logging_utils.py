import logging
import logging.config
from pythonjsonlogger import jsonlogger
from settings import LOG_LEVEL
import sys


def init_logger(name):
    logger = logging.getLogger(name)
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(levelname)s %(name)s %(message)s ", timestamp=True
    )
    logHandler = logging.StreamHandler(sys.stdout)
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False
    return logger
