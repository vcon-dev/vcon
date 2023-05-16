import uvicorn
from lib.logging_utils import init_logger
from settings import HOSTNAME
import urllib
import asyncio
import uvicorn
from conserver import conserver_app
from main_loop import scheduler_app

logger = init_logger(__name__)

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
        log_level="trace",
        workers=1, 
        loop="asyncio",
        host=host_ip, 
        port=port_num, 
        reload=True))

    api = asyncio.create_task(server.serve())
    sched = asyncio.create_task(scheduler_app.serve())

    await asyncio.wait([sched, api])

if __name__ == "__main__":
    asyncio.run(main())
