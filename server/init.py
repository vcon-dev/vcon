import uvicorn
import logging
from lib.logging_utils import init_logger
from settings import HOSTNAME
import urllib
import asyncio
import uvicorn
from rocketry import Rocketry
from fastapi.applications import FastAPI

logging.config.fileConfig("./logging.conf")


# Load FastAPI app
conserver_app = FastAPI()
FastAPI.conserver_app = conserver_app
scheduler = Rocketry(execution="async")
FastAPI.scheduler = scheduler
logger = init_logger(__name__)

# Now load all the modules
import api  # noqa
import admin  # noqa
import lifecycle  # noqa



class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        scheduler.session.shut_down()
        return super().handle_exit(sig, frame)

async def main():
    "Run scheduler and the API"
    url_parser = urllib.parse.urlparse(HOSTNAME)
    host_ip = url_parser.hostname
    port_num = url_parser.port
    logger.info("Conserver binding to host: {} port: {}".format(host_ip, port_num))

    server = Server(config=uvicorn.Config(
        app=conserver_app, 
        log_level="trace",
        workers=1, 
        loop="asyncio",
        host=host_ip, 
        port=port_num, 
        reload=True))

    api = asyncio.create_task(server.serve())
    sched = asyncio.create_task(scheduler.serve())

    await asyncio.wait([sched, api])

if __name__ == "__main__":
    asyncio.run(main())
