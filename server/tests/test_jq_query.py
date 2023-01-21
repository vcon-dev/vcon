
import os
import logging
import json
import fastapi.testclient
import pytest

import conserver
import vcon
import conserver_test

logging.config.fileConfig('tests/logging.conf')
logger = logging.getLogger(__name__)


#@pytest.mark.incremental
@pytest.mark.dependency
#@pytest.mark.dependency(depends=["test_1_post_dialog_vcon"])
def test_2_jq():
  logger.debug("Starting test_2_jq")
  with fastapi.testclient.TestClient(conserver.app) as client:
    query = {}
    #query["jq_transform"] = "[inputs | select(.dialog) | url, filename, mimetype]"
    query["jq_transform"] = ".dialog[].url, .dialog[].mimetype, .dialog[].filename"
    #query["jq_transform"] = ".dialog"
    response = client.get("/vcon/{}/jq".format(conserver_test.UUID), params=query)
    assert(response.status_code == 200)
    print("text: " + response.text)
    print("response dir: {}".format(dir(response)))

    dialog_array = json.loads(response.text)
    assert(len(dialog_array) == 3)
    assert(response.text == str(response.content, "utf-8"))
    assert(dialog_array[0] == conserver_test.url)
    assert(dialog_array[1] == vcon.Vcon.MIMETYPE_AUDIO_WAV)
    assert(dialog_array[2] == os.path.basename(conserver_test.file_path))

  logger.debug("Exiting test_2_jq")

