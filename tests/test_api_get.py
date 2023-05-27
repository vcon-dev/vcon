import requests

def test_get_items():
    # Make a GET request to the FastAPI route
    response = requests.get("http://localhost:8000/vcon")

    # Assert the response status code
    assert response.status_code == 200
    print(response.json())
