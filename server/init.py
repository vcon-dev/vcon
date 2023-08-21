import uvicorn
from lib.logging_utils import init_logger
from settings import HOSTNAME
import urllib
import asyncio
from conserver import conserver_app
from main_loop import scheduler_app
from lib.error_tracking import init_error_tracker

logger = init_logger(__name__)
init_error_tracker()

class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        scheduler_app.session.shut_down()
        return super().handle_exit(sig, frame)

async def main():
    "Run scheduler and the API"
    url_parser = urllib.parse.urlparse(HOSTNAME)
    host_ip = url_parser.hostname
    port_num = url_parser.port
    logger.info("Conserver binding to host: {} port: {}".format(host_ip, port_num))

    server = Server(config=uvicorn.Config(
        app=conserver_app,
        loop="asyncio",
        host=host_ip, 
        port=port_num, 
        reload=True))

    api = asyncio.create_task(server.serve())
    sched = asyncio.create_task(scheduler_app.serve())

    await asyncio.wait([sched, api])

if __name__ == "__main__":
    asyncio.run(main())
