from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import asyncio
from lib.logging_utils import init_logger

import fastapi.testclient
import conserver

app = conserver.conserver_app
client = TestClient(app)


def test_api_get_vcons():
    response = client.get("/")
    print("response: {}".format(response))
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
