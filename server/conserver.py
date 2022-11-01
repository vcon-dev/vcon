import logging
import logging.config
import uvicorn
from fastapi.applications import FastAPI


logger = logging.getLogger(__name__)
logging.config.fileConfig('./logging.conf')
logger.info('Conserver starting up')

# Load FastAPI app
app = FastAPI()
FastAPI.conserver_app = app
import api
import lifecycle

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

