import settings
import yaml

_config: dict = None


def get_config() -> dict:
    """ This is to keep logic of accessing config in one place """
    global _config
    if not _config:
        with open(settings.CONSERVER_CONFIG_FILE) as file:
            _config = yaml.safe_load(file)
    return _config


class Configuration:
    @classmethod
    def get_config(cls) -> dict:
        return get_config()

    @classmethod
    def get_storages(cls) -> dict:
        config = cls.get_config()
        return config.get("storages", {})
