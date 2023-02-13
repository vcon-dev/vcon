import os
from lib.logging_utils import init_logger
import json
import fastapi.testclient
import pytest

import conserver
import vcon
import conserver_test

logger = init_logger(__name__)


# @pytest.mark.incremental
@pytest.mark.dependency
# @pytest.mark.dependency(depends=["test_1_post_dialog_vcon"])
def test_2_json_path():
    logger.debug("Starting test_2_json_path")
    with fastapi.testclient.TestClient(conserver.app) as client:
        query = {}
        query["path_string"] = "$.dialog[0]"
        response = client.get(
            "/vcon/{}/JSONPath".format(conserver_test.UUID), params=query
        )
        assert response.status_code == 200
        print("text: " + response.text)
        print("response dir: {}".format(dir(response)))

        dialog_array = json.loads(response.text)
        assert len(dialog_array) == 1
        assert response.text == str(response.content, "utf-8")
        assert dialog_array[0]["url"] == conserver_test.url
        assert dialog_array[0]["mimetype"] == vcon.Vcon.MIMETYPE_AUDIO_WAV
        assert dialog_array[0]["filename"] == os.path.basename(conserver_test.file_path)

    logger.debug("Exiting test_2_json_path")
