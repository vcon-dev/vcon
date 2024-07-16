import pytest
import os
import json
# import sys
from . import save
import redis_mgr

@pytest.fixture(scope="function")
def vcon_input(fixture_name):
    file_path = os.path.join(os.path.dirname(__file__), f'../../links/test_dataset/{fixture_name}.json')
    with open(file_path, 'r') as f:
        return json.load(f)


@pytest.mark.parametrize("fixture_name", ["vcon_fixture"])
def test_save(vcon_input):
    vcon = vcon_input
    opts = {
        "organization_key": os.environ["OPENAI_ORG"],
        "project_key": os.environ["OPENAI_PROJECT"],
        "api_key": os.environ["OPENAI_QA_API_KEY"],
        "purpose": "assistants",
        "vector_store_id": os.environ["OPENAI_VECTOR_STORE_ID"]
    }
    redis_mgr.set_key(f"vcon:{vcon["uuid"]}", vcon)
    save(vcon["uuid"], opts)
    assert "Finished chatgpt storage for vCon: 1ba06c0c-97ea-439f-8691-717ef86e4f3e"


