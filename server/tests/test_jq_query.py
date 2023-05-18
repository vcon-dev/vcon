import os
from lib.logging_utils import init_logger
import json
import fastapi.testclient
import pytest

import conserver
import vcon
import conserver_test
import pyjq

logger = init_logger(__name__)

# simple test to be sure pyjq is installed correctly and working
def test_2_jq():
  json_dict = {"a": "bbb"}
  result = pyjq.all(".a", json_dict)
  assert(result[0] == "bbb")

# @pytest.mark.incremental
@pytest.mark.dependency
# @pytest.mark.dependency(depends=["test_1_post_dialog_vcon"])
def test_2_jq_entrypoint():
    logger.debug("Starting test_2_jq")
    with fastapi.testclient.TestClient(conserver.conserver_app) as client:
        query = {}
        # query["jq_transform"] = "[inputs | select(.dialog) | url, filename, mimetype]"
        query["jq_transform"] = ".dialog[].url, .dialog[].mimetype, .dialog[].filename"
        # query["jq_transform"] = ".dialog"
        response = client.get("/vcon/{}/jq".format(conserver_test.UUID), params=query)
        assert response.status_code == 200
        print("text: " + response.text)
        print("response dir: {}".format(dir(response)))

        dialog_array = json.loads(response.text)
        assert len(dialog_array) == 3
        assert response.text == str(response.content, "utf-8")
        assert dialog_array[0] == conserver_test.url
        assert dialog_array[1] == vcon.Vcon.MIMETYPE_AUDIO_WAV
        assert dialog_array[2] == os.path.basename(conserver_test.file_path)

    logger.debug("Exiting test_2_jq")
