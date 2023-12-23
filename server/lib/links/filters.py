import json
import random
from lib.logging_utils import init_logger

logger = init_logger(__name__)


def is_included(options, _vcon):
    if not options:
        return True
    if not options.get("only_if"):
        return True
    filter = options["only_if"]
    section = filter["section"]
    type = filter["type"]
    includes = filter["includes"]

    try:
        for element in getattr(_vcon, section):
            if not element["type"] == type:
                continue
            if type == "tags":
                tags = json.loads(element["body"])
                if includes in tags:
                    return True
            elif includes in element["body"]:
                return True
    except Exception as e:
        logger.error(f"Error checking inclusion: {e}")
    return False


def randomly_execute_with_sampling(options):
    if options.get("sampling_rate"):
        if random.random() < options["sampling_rate"]:
            return True
        else:
            return False
    return True
