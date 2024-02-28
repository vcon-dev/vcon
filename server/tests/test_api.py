from fastapi.testclient import TestClient
from vcon_fixture import generate_mock_vcon
import pytest
import server.api as api


def post_vcon(vcon):
    # Use the TestClient to make requests to the app.
    with TestClient(api.app) as client:
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
    with TestClient(api.app) as client:
        response = client.get("/vcon/{}".format(test_vcon["uuid"]))
        assert response.status_code == 200
        print("response: {}".format(response))

    # Delete the vcon using the test client
    with TestClient(api.app) as client:
        response = client.delete("/vcon/{}".format(test_vcon["uuid"]))
        assert response.status_code == 204
        print("response: {}".format(response))

    # Read the vcon back
    with TestClient(api.app) as client:
        response = client.get("/vcon/{}".format(test_vcon["uuid"]))
        assert response.status_code == 404
        print("response: {}".format(response))


@pytest.mark.anyio
def test_get_vcons():
    vcon_uuids = []
    # Write a dozen vcons and read them back
    for i in range(12):
        test_vcon = generate_mock_vcon()
        post_vcon(test_vcon)
        vcon_uuids.append(test_vcon["uuid"])

    # Read the vcons back using the test client, deleting them as we go
    with TestClient(api.app) as client:
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
