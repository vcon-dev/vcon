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
def test_get_vcons():

    vcon_uuids = []
    # Write a dozen vcons and read them back
    for i in range(12):
        test_vcon = generate_mock_vcon()
        post_vcon(test_vcon)
        vcon_uuids.append(test_vcon["uuid"])

    # Read the vcons back using the test client, deleting them as we go
    with TestClient(app) as client:
        # Get the list of vCons from the server
        response = client.get("/vcon")
        assert response.status_code == 200
        print("response: {}".format(response))

        # Take the list of vCons, check to see if they are in the list
        # of vCons we created, and delete them
        vcon_list = response.json()
        for vcon_id in vcon_list:
            assert vcon_id in vcon_uuids
            response = client.delete("/vcon/{}".format(vcon_id))
            assert response.status_code == 204
            print(f"API response for {vcon_id}: {response}")
