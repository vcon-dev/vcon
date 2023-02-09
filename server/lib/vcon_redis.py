import redis.asyncio as redis
from redis.commands.json.path import Path
import vcon
import json
from typing import Optional
from lib.logging_utils import init_logger
from lib.phone_number_utils import get_e164_number

logger = init_logger(__name__)


class VconRedis:
    """Encapsulate vcon redis operation
    """

    def __init__(self, redis_url=None, redis_client=None):
        if redis_url:
            self._redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        elif redis_client:
            self._redis_client = redis_client
        else:
            raise Exception("Aurguments for VconRedis missing. redis_url or redis_client is required.")


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
        vcon_dict = await self._redis_client.json().get(f"vcon:{vcon_id}", Path.root_path())
        if not vcon_dict:
            return None
        _vcon = vcon.Vcon()
        _vcon.loads(json.dumps(vcon_dict))
        return _vcon


    async def get_vcon_by_bria_id(self, bria_id: str) -> Optional[vcon.Vcon]:
        """Retrives the vcon from redis for givin bria_id

        Args:
            bria_id (str): bria id

        Returns:
            Optional[vcon.Vcon]: Returns vocon for given bria id
        """
        # lookup the vCon in redis using bria ID
        # FT.SEARCH idx:adapterIdsIndex '@adapter:{bria} @id:{f8be045704cb4ea98d73f60a88590754}'
        result = await self._redis_client.ft(index_name="idx:adapterIdsIndex").search(
            f"@adapter:{{bria}} @id:{{{bria_id}}}"
        )
        if len(result.docs) <= 0:
            return
        v_con = vcon.Vcon()
        v_con.loads(result.docs[0].json)
        return v_con
    

    async def get_same_leg_or_new_vcon(self, body) -> vcon.Vcon:
        """Try to detect if this is the same call and if so don't create a new vCon but add this
            as a call stage to the existing vCon

        Returns:
            vcon.Vcon: New or existing vcon
        """
        redis_key = self.call_leg_detection_key(body)
        logger.info("computed_redis_key is %s", redis_key)
        vcon_id = await self._redis_client.get(redis_key)
        v_con = None
        if vcon_id:
            v_con = await self.get_vcon(vcon_id)
            logger.info(f"Found the key {redis_key} - Updating the existing vcon")
        else:
            v_con = vcon.Vcon()
            await self._redis_client.set(redis_key, v_con.uuid)
            logger.info(f"Key NOT found {redis_key}- Created a new vcon")

        logger.info(f"The vcon id is {v_con.uuid}")
        await self._redis_client.expire(redis_key, 60)
        return v_con

    
    def call_leg_detection_key(self, body):
        dealer_number = get_e164_number(body.get("dialerId"))
        customer_number = get_e164_number(body.get("customerNumber"))
        return f"bria:{dealer_number}:{customer_number}"


    async def persist_call_leg_detection_key(self, body):
        key = self.call_leg_detection_key(body)
        logger.info(f"Trying to persist the key - {key}")
        if (await self._redis_client.exists(key)):
            await self._redis_client.persist(key)
            logger.info(f"Persisted the key - {key}")   