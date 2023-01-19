import os
import pytest
import logging
import fastapi.testclient
import datetime
import json

import conserver
import vcon

logging.config.fileConfig('tests/logging.conf')
logger = logging.getLogger(__name__)

UUID = "01855517-ac4e-8edf-84fd-77776666acbe"

file_path = "../examples/agent_sample.wav"

url = "https://github.com/vcon-dev/vcon/blob/main/examples/agent_sample.wav?raw=true"


#@pytest.mark.incremental
@pytest.mark.dependency
#@pytest.mark.dependency(depends=["TestTranscribe::test_2_get_dialog_vcon"])
def test_1_post_dialog_vcon():
  logger.debug("Starting test_1_post_dialog_vcon")
  with fastapi.testclient.TestClient(conserver.app) as client:
    vCon = vcon.Vcon()
    first_party = vCon.set_party_parameter("tel", "1234")
    second_party = vCon.set_party_parameter("tel", "5678")

    file_content = b""
    with open(file_path, "rb") as file_handle:
      file_content = file_handle.read()
      print("body length: {}".format(len(file_content)))
      assert(len(file_content) > 10000)

    dialog_index = vCon.add_dialog_external_recording(file_content,
      datetime.datetime.utcnow(),
      0, # duration TODO
      [0,1],
      url,
      vcon.Vcon.MIMETYPE_AUDIO_WAV,
      os.path.basename(file_path))
    # hack the UUID so we have a predictable UUID and we don't polute the DB
    vCon._vcon_dict["uuid"] = UUID
    uuid = vCon.uuid
    assert(uuid == UUID)
    vcon_json_string = vCon.dumps()
    vcon_json_object = json.loads(vcon_json_string)
    print("created vcon: {}".format(vcon_json_object))

    response = client.post("/vcon", json=vcon_json_object)
    assert(response.status_code == 200)
    print("text: " + response.text)
    print("response dir: {}".format(dir(response)))
    assert(response.text == str(response.content, "utf-8"))
    saved_vcon = vcon.Vcon()
    saved_vcon.loads(response.text)
    assert(saved_vcon.parties[0]["tel"] == "1234")
    assert(saved_vcon.parties[1]["tel"] == "5678")
    assert(len(saved_vcon.dialog) == 1)
    assert(saved_vcon.dialog[0]["url"] == url)
    assert(len(saved_vcon.analysis) == 0)

  logger.debug("Exiting test_1_post_dialog_vcon")

