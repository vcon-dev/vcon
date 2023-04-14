import pytest
import asyncio
from lib.logging_utils import init_logger

import fastapi.testclient
import conserver

logger = init_logger(__name__)


def test_get_docs():
    logger.debug("Starting test_get_docs")
    with fastapi.testclient.TestClient(conserver.conserver_app) as client:
        print("{} client type: {}".format(__name__, type(client)))
        response = client.get("/docs")
        assert response.status_code == 200

        if response.status_code != 200:
            pytest.exit(
                "Basic conserver FastApi framework not working.  Aborting all tests."
            )

    try:
        asyncio.all_tasks()
        raise Exception("Should not get here as loop should have been closed down")

    except RuntimeError as rt_error:
        assert str(rt_error) == str(RuntimeError("no running event loop"))

    logger.debug("Exiting test_get_docs")
