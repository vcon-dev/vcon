import pytest
import redis.asyncio as redis
from server.lib.vcon_redis import VconRedis

from adapters.bria import get_same_leg_or_new_vcon

from settings import REDIS_URL


@pytest.mark.asyncio
async def test_it_shouldnt_break_when_there_is_no_vcon():
    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    vcon_redis = VconRedis(redis_client=r)

    fake_vcon = {}
    result = await get_same_leg_or_new_vcon(r, fake_vcon, vcon_redis)
    print(result)
    assert True
