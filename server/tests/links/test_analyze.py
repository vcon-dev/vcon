import pytest
from unittest.mock import patch, AsyncMock

from server.links import analyze
import vcon

# Construct empty vCon


def vcon_factory():
    vCon = vcon.Vcon()
    vCon.add
    return vCon


@pytest.mark.asyncio
@patch("server.lib.vcon_redis.VconRedis")
@patch("server.lib.vcon_redis.VconRedis.get_vcon")
@patch("server.lib.vcon_redis.VconRedis.store_vcon")
async def test_link_analyze(mocked_vcon_redis, mocked_get_vcon, mocked_store_vcon):
    vcon_object = vcon_factory()
    mocked_get_vcon.return_value = AsyncMock(return_value=vcon_object)
    mocked_store_vcon.return_value = AsyncMock(return_value=vcon_object)
    # Your test code here
    opts = {"OPENAI_API_KEY": "fake-key"}
    result = await analyze.run(vcon_uuid="fake-id", opts=opts)
    assert result == "fake-result"
