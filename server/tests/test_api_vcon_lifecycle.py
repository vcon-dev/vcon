from fastapi.testclient import TestClient
from vcon_fixture import generate_mock_vcon
import pytest
import httpx


# import conserver
# app = conserver.conserver_app


def post_vcon(vcon):
    response = httpx.post("http://localhost:8000/vcon", json=vcon)
    print("response: {}".format(response))
    assert response.status_code == 200

@pytest.mark.anyio
def test_api_vcon_lifecycle():

   # Write a dozen vcons
    test_vcon = generate_mock_vcon()
    post_vcon(test_vcon)

    # Read the vcon back
    response = httpx.get("http://localhost:8000/vcon/{}".format(test_vcon["uuid"]))
    assert response.status_code == 200
    print("response: {}".format(response))

    # Delete the vcon
    response = httpx.delete("http://localhost:8000/vcon/{}".format(test_vcon["uuid"]))
    assert response.status_code == 200

    # Read the vcon back
    response = httpx.get("http://localhost:8000/vcon/{}".format(test_vcon["uuid"]))
    assert response.status_code == 404

