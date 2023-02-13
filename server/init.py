import uvicorn
import logging
from settings import HOSTNAME
import urllib

logging.config.fileConfig("./logging.conf")

if __name__ == "__main__":
    url_parser = urllib.parse.urlparse(HOSTNAME)
    host_ip = url_parser.hostname
    port_num = url_parser.port
    print("uvicorn binding to host: {} port: {}".format(host_ip, port_num))
    uvicorn.run("conserver:app", host=host_ip, port=port_num, reload=True)
