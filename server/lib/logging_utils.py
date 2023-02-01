import logging
import logging.config
from settings import LOG_LEVEL

def init_logger(name):
    # create a formatter
    formatter = logging.Formatter('\033[31m%(levelname)s\033[0m: %(message)s')
    # create a handler for the error messages
    error_handler = logging.StreamHandler()
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger().addHandler(error_handler)

    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    return logger

