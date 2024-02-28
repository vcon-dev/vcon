import pytest
from unittest.mock import patch, AsyncMock

from links import analyze


@pytest.mark.asyncio
@patch("server.lib.vcon_redis.VconRedis.get_vcon")
@patch("server.lib.vcon_redis.VconRedis.store_vcon")
async def test_link_analyze(mocked_get_vcon, mocked_store_vcon):
    mocked_get_vcon.return_value = AsyncMock(return_value="content of the VCON")
    mocked_store_vcon.return_value = AsyncMock(return_value="content of the VCON")
    # Your test code here
    opts = {"OPENAI_API_KEY": "fake-key"}
    result = await analyze.run(vcon_uuid="fake-id", opts=opts)
    assert result == "fake-result"
