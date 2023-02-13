import redis.asyncio as redis
from redis.commands.json.path import Path
import vcon
import json
from typing import Optional
from lib.logging_utils import init_logger
from lib.phone_number_utils import get_e164_number

logger = init_logger(__name__)


class VconRedis:
    """Encapsulate vcon redis operation"""

    def __init__(self, redis_url=None, redis_client=None):
        if redis_url:
            self._redis_client = redis.from_url(
                redis_url, encoding="utf-8", decode_responses=True
            )
        elif redis_client:
            self._redis_client = redis_client
        else:
            raise Exception(
                "Aurguments for VconRedis missing. redis_url or redis_client is required."
            )

    async def store_vcon(self, vCon: vcon.Vcon):
        """Stores the vcon into redis

        Args:
            vCon (vcon.Vcon): this vCon gets stored in redis
        """
        key = f"vcon:{vCon.uuid}"
        cleanvCon = json.loads(vCon.dumps())
        await self._redis_client.json().set(key, Path.root_path(), cleanvCon)

    async def get_vcon(self, vcon_id: str) -> Optional[vcon.Vcon]:
        """Retrives the vcon from redis for given vcon_id

        Args:
            vcon_id (str): vcon id

        Returns:
            Optional[vcon.Vcon]: Returns vcon for givin vcon id or None if vcon is not present.
        """
        vcon_dict = await self._redis_client.json().get(
            f"vcon:{vcon_id}", Path.root_path()
        )
        if not vcon_dict:
            return None
        _vcon = vcon.Vcon()
        _vcon.loads(json.dumps(vcon_dict))
        return _vcon
