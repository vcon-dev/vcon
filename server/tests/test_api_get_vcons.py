from lib.logging_utils import init_logger
logger = init_logger(__name__)
import httpx

def test_api_get_vcons():
    response = httpx.get("http://localhost:8000/vcon")
    assert response.status_code == 200