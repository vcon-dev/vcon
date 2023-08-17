from fastapi.testclient import TestClient
from vcon_fixture import generate_mock_vcon
import pytest
import conserver
app = conserver.conserver_app


def post_vcon(vcon):
    # Use the TestClient to make requests to the app.
    with TestClient(app) as client:
        response = client.post("/vcon", json=vcon)
        assert response.status_code == 201
        print("response: {}".format(response))
        return response

@pytest.mark.anyio
def test_api_vcon_lifecycle():

   # Write a dozen vcons
    test_vcon = generate_mock_vcon()
    post_vcon(test_vcon)

    # Read the vcon back using the test client
    with TestClient(app) as client:
        response = client.get("/vcon/{}".format(test_vcon["uuid"]))
        assert response.status_code == 200
        print("response: {}".format(response))


    # Delete the vcon using the test client
    with TestClient(app) as client:
        response = client.delete("/vcon/{}".format(test_vcon["uuid"]))
        assert response.status_code == 204
        print("response: {}".format(response))

    # Read the vcon back
    with TestClient(app) as client:
        response = client.get("/vcon/{}".format(test_vcon["uuid"]))
        assert response.status_code == 404
        print("response: {}".format(response))

