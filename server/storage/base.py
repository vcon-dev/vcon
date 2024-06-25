import importlib
import types
import time
from typing import Optional

from lib.logging_utils import init_logger
from config import get_config


_imported_modules: dict[str, types.ModuleType] = {}


logger = init_logger(__name__)


def log_metrics(func):
    """Decorator to log the time taken to run the storage module"""

    def wrapper(self, vcon_id):
        started = time.time()
        logger.info(
            "Running storage %s module %s %s for vCon: %s",
            self.storage_name,
            self.module_name,
            func.__name__,
            vcon_id,
        )
        result = func(self, vcon_id)
        storage_processing_time = round(time.time() - started, 3)
        logger.info(
            "Finished storage %s module %s %s for vCon: %s in %s seconds.",
            self.storage_name,
            self.module_name,
            func.__name__,
            vcon_id,
            storage_processing_time,
            extra={"storage_processing_time": storage_processing_time},
        )
        return result

    return wrapper


class Storage:
    options: dict = None
    module: types.ModuleType = None
    module_name: str = None
    storage_name: str = None

    def __init__(self, storage_name: str) -> None:
        self.storage_name = storage_name
        config = get_config()
        storage = config["storages"][self.storage_name]
        self.module_name = storage["module"]

        if self.module_name not in _imported_modules:
            _imported_modules[self.module_name] = importlib.import_module(
                self.module_name
            )
        self.module = _imported_modules[self.module_name]
        self.options = storage.get("options", self.module.default_options)

    @log_metrics
    def save(self, vcon_id) -> None:
        self.module.save(vcon_id, self.options)

    @log_metrics
    def get(self, vcon_id) -> Optional[dict]:
        if hasattr(self.module, "get"):
            return self.module.get(vcon_id, self.options)
        return None
