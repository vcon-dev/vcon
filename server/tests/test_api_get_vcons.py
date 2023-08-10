import httpx
def test_api_get_vcons():
    response = httpx.get("http://localhost:8000/vcon")
    assert response.status_code == 200