import os 
import sys
import uuid
import pytest
import pytest_asyncio
import random
import string
sys.path.append("server")
import redis_mgr

# Run before each test function
@pytest_asyncio.fixture(autouse=True)
async def setup_teardown():
    # Before test
    redis_mgr.create_pool()

    yield

    # after test
    await redis_mgr.shutdown_pool()

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

@pytest.mark.asyncio
async def test_get_and_read():
    print(sys.path)
    random_bytes = get_random_string(10)
    random_key = get_random_string(10)
    await redis_mgr.set_key(random_key, random_bytes)
    read_back = await redis_mgr.get_key(random_key)
    assert(read_back==random_bytes)
    await redis_mgr.delete_key(random_key)
    result = await redis_mgr.get_key(random_key)
    assert(result==None)

@pytest.mark.asyncio
async def test_unit_key():
    random_key = get_random_string(10)
    result = await redis_mgr.get_key(random_key)
    assert(result==None)

@pytest.mark.asyncio
async def test_empty_key():
    try:
        result = await redis_mgr.get_key("")
    except Exception as e:
        assert(type(e)==TypeError)

