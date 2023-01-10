import pytest

import fastapi.testclient

import conserver

client = fastapi.testclient.TestClient(conserver.app)

def test_get_docs():
  response = client.get("/docs")
  assert(response.status_code == 200)

  if(response.status_code != 200):
    pytest.exit("Basic conserver FastApi framework not working.  Aborting all tests.")



