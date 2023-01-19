import os
import pytest
import datetime
import fastapi.testclient
import json
import logging
import asyncio

import vcon
import conserver
import lifecycle
import redis_mgr

logging.config.fileConfig('tests/logging.conf')
logger = logging.getLogger(__name__)

UUID = "01855517-ac4e-8edf-84fd-77776666acbe"

#got_client = fastapi.testclient.TestClient(conserver.app)
#def get_client():
#  return(got_client)

def delete_test_vcon():
  #delete_response = get_client().delete("/vcon/{}".format(UUID))
  #print("delete response: {}".format(delete_response.status_code))
  pass

# Run before each test function
@pytest.fixture(autouse=True)
def setup_teardown():
  # Before test
  redis_mgr.create_pool()
  lifecycle.task_monitor.show_running_tasks()
  lifecycle.task_monitor.schedule()

  dialog_count = 0
  #get_response = client.get("/vcon/{}".format(UUID), headers={ "accept" : "application/json"})
  #assert(get_response.status_code == 200)
  #get_json_object = get_response.json()
  #if(get_json_object is None):
  #  # try again
  #  get_response = client.get("/vcon/{}".format(UUID), headers={ "accept" : "application/json"})
  #  assert(get_response.status_code == 200)
  #  get_json_object = get_response.json()

  #if(get_json_object is not None):
  #  dialog_count = len(get_json_object.get("dialog", []))
  #  assert(dialog_count == 1)
  #  assert(get_json_object["dialog"][0]["url"] == TestTranscribe.url)
  #else:
  #  dialog_count = 0
  print("start dialogs: {} (should be 0)".format(dialog_count))
  delete_test_vcon()

  yield

  # After test
  #get_response = client.get("/vcon/{}".format(UUID), headers={ "accept" : "application/json"})
  #assert(get_response.status_code == 200)
  #get_json_object = get_response.json()
  #if(get_json_object is None):
  #  # try again
  #  get_response = client.get("/vcon/{}".format(UUID), headers={ "accept" : "application/json"})
  #  assert(get_response.status_code == 200)
  #  get_json_object = get_response.json()

  #if(get_json_object is not None):
  #  dialog_count = len(get_json_object.get("dialog", []))
  #  assert(dialog_count == 1)
  #  assert(get_json_object["dialog"][0]["url"] == TestTranscribe.url)
  #else:
  #  dialog_count = 0
  redis_mgr.shutdown_pool()
  lifecycle.task_monitor.stop()
  lifecycle.task_monitor.show_running_tasks()
  print("done dialogs: {} (should be 0)".format(dialog_count))
  #delete_test_vcon()

#@pytest.fixture(scope="function")
#def client():
#  print("New client")
#  return(fastapi.testclient.TestClient(conserver.app))

#def pytest_runtest_makereport(item, call):
#    if "incremental" in item.keywords:
#        if call.excinfo is not None:
#            parent = item.parent
#            parent._previousfailed = item
#
#def pytest_runtest_setup(item):
#    previousfailed = getattr(item.parent, "_previousfailed", None)
#    if previousfailed is not None:
#        pytest.xfail("previous test failed (%s)" % previousfailed.name)

class TestTranscribe:
  test_get_dialog_vcon = {}
  file_path = "../examples/agent_sample.wav"
  url = "https://github.com/vcon-dev/vcon/blob/main/examples/agent_sample.wav?raw=true"
  _transcribe_runs = 0


  def test_2_get_dialog_vcon(self):
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    #assert(loop.is_running())
    assert(not loop.is_closed())
    with fastapi.testclient.TestClient(conserver.app) as client:
      print("{} client type: {}".format(__name__, type(client)))
      get_response = client.get("/vcon/{}".format(UUID), headers={ "accept" : "application/json"})
      print("get response: {}".format(get_response))
      print("response stream consumed: {}".format(get_response.is_stream_consumed))
      print("response text: {}".format(get_response.text))
      print("response content length: {}".format(len(get_response.content)))
      assert(get_response.status_code == 200)
      get_json_object = get_response.json()
      if(get_json_object is None):
        # try again
        print("WARNING: re-getting /vcon/{}".format(UUID))
        get_response = client.get("/vcon/{}".format(UUID), headers={ "accept" : "application/json"})
        assert(get_response.status_code == 200)
        get_json_object = get_response.json()

      assert(len(get_json_object["dialog"]) == 1)
      assert(get_json_object["dialog"][0]["url"] == TestTranscribe.url)
      #assert(get_json_object == TestTranscribe.vcon_json_object)

      #assert(loop.is_running())
      #assert(not loop.is_closed())

  #@pytest.mark.incremental
  @pytest.mark.dependency
  #@pytest.mark.dependency(depends=["tests/test_post_dialog.py::test_1_post_dialog_vcon"])
  def test_21_get_dialog_vcon(self):
    try:
      get_response = None
      loop = asyncio.get_event_loop()
      loop.set_debug(True)
      assert(not loop.is_running())
      #assert(loop.is_closed())
      with fastapi.testclient.TestClient(conserver.app) as client:
        assert(not loop.is_closed())
        logger.info("starting test_21_get_dialog_vcon")
        get_response = client.get("/vcon/{}".format(UUID), headers={ "accept" : "application/json"})
        get_json_object = get_response.json()
        if(get_json_object is None):
          # try again
          print("WARNING: re-getting /vcon/{}".format(UUID))
          get_response = client.get("/vcon/{}".format(UUID), headers={ "accept" : "application/json"})
          assert(get_response.status_code == 200)
          get_json_object = get_response.json()

        assert(get_response is not None)

    except RuntimeError as rt_error:
      assert(str(rt_error) == str(RuntimeError("Event loop is closed")))
      assert(get_response is not None)

    print("get response: {}".format(get_response))
    print("response stream consumed: {}".format(get_response.is_stream_consumed))
    print("response text: {}".format(get_response.text))
    print("response content length: {}".format(len(get_response.content)))
    assert(get_response.status_code == 200)
    assert(len(get_json_object["dialog"]) == 1)
    assert(get_json_object["dialog"][0]["url"] == TestTranscribe.url)
    #assert(get_json_object == TestTranscribe.vcon_json_object)
    logger.info("exiting test_21_get_dialog_vcon")

  #@pytest.mark.incremental
  #@pytest.mark.dependency
  @pytest.mark.dependency(depends=["TestTranscribe::test_21_get_dialog_vcon"])
  def test_3_transcribe_whisper(self):
      loop = asyncio.get_event_loop()
      loop.set_debug(True)
      with fastapi.testclient.TestClient(conserver.app) as client:
        query_parameters = { "plugin" : "plugins.transcribe" }
        transcribe_response = client.patch("/vcon/{}".format(UUID), params=query_parameters)
        TestTranscribe._transcribe_runs += 1
        if(transcribe_response.status_code != 200):
          print("patch error: {}".format(transcribe_response.text))

        assert(transcribe_response.status_code == 200)

        transcribed_vcon = vcon.Vcon()
        transcribed_vcon.loads(transcribe_response.text)
        assert(transcribed_vcon.uuid == UUID)
        assert(len(transcribed_vcon.analysis) == TestTranscribe._transcribe_runs * 3)

  @pytest.mark.dependency(depends=["TestTranscribe::test_21_get_dialog_vcon"])
  def test_4_transcribe_whisper(self):
      loop = asyncio.get_event_loop()
      loop.set_debug(True)
      with fastapi.testclient.TestClient(conserver.app) as client:
        query_parameters = { "plugin" : "plugins.transcribe" }
        transcribe_response = client.patch("/vcon/{}".format(UUID), params=query_parameters)
        TestTranscribe._transcribe_runs += 1
        assert(transcribe_response.status_code == 200)

        transcribed_vcon = vcon.Vcon()
        transcribed_vcon.loads(transcribe_response.text)
        assert(transcribed_vcon.uuid == UUID)
        assert(len(transcribed_vcon.analysis) == TestTranscribe._transcribe_runs * 3)

