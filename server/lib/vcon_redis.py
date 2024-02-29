from typing import Optional
from lib.logging_utils import init_logger
from redis.commands.json.path import Path
from redis_mgr import redis
import vcon

logger = init_logger(__name__)


class VconRedis:
    """Encapsulate vcon redis operation"""

    def store_vcon(self, vCon: vcon.Vcon):
        """Stores the vcon into redis

        Args:
            vCon (vcon.Vcon): this vCon gets stored in redis
        """
        key = f"vcon:{vCon.uuid}"
        cleanvCon = vCon.to_dict()
        redis.json().set(key, Path.root_path(), cleanvCon)

    def get_vcon(self, vcon_id: str) -> Optional[vcon.Vcon]:
        """Retrives the vcon from redis for given vcon_id

        Args:
            vcon_id (str): vcon id

        Returns:
            Optional[vcon.Vcon]: Returns vcon for givin vcon id or None if vcon is not present.
        """
        vcon_dict = redis.json().get(
            f"vcon:{vcon_id}", Path.root_path()
        )
        if not vcon_dict:
            return None
        _vcon = vcon.Vcon(vcon_dict)
        return _vcon
