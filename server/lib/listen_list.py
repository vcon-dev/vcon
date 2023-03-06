from lib.logging_utils import init_logger

logger = init_logger(__name__)


async def listen_list(r, list_name):
    while True:
        values = await r.blpop([list_name])
        logger.info(f"Got the value {values}")
        if values:
            yield values[1]
