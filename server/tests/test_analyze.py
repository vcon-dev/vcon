from unittest.mock import patch
from links.analyze import run
from lib.vcon_redis import VconRedis

import vcon

# TODO Create an example of the expected vcon data (get from DB and remove sensitive data)

#@pytest.mark.asyncio
#@patch("server.links.analyze.VconRedis.get_vcon")
#@patch("server.links.analyze.VconRedis.store_vcon")
@patch("openai.ChatCompletion.create")
def test_link_analyze(mocked_openai_chat_completion_create, mocked_store_vcon, mocked_get_vcon):
#def test_link_analyze(mocked_openai_chat_completion_create, mocked_store_vcon, mocked_get_vcon):
    # TODO create test vcon and save it to Redis
    vcon_object = vcon.Vcon.build_new()
    VconRedis().store_vcon(vcon_object)
    #mocked_get_vcon.return_value = vcon_object
    #mocked_store_vcon.return_value = vcon_object
    mocked_openai_chat_completion_create.return_value = {"choices": [{"message": {"content": "fake-result"}}]}
    # Your test code here
    opts = {"OPENAI_API_KEY": "fake-key"}
    result = run(vcon_uuid="fake-vcon-id", link_name="fake-analysis", opts=opts)
    assert result == "fake-vcon-id"
    # TODO Get Vcon for redis and make sure it was updated as expected
    VconRedis().get_vcon(vcon_object)
    mocked_store_vcon.assert_called_once_with({})

