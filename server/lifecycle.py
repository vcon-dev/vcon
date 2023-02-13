from lib.logging_utils import init_logger

from fastapi.applications import FastAPI
from lifecycle_helpers import check_sqs, load_adaptors, load_pipelines, update_available_blocks
from lib.process_utils import start_async_process

logger = init_logger(__name__)
logger.info("Conserver starting up")

# Load FastAPI app

PROCESSES = []


app = None
if hasattr(FastAPI, 'conserver_app'):
    app = FastAPI.conserver_app
    
    @app.on_event("startup")
    async def startup():
        try:
            global PROCESSES
            process1 = start_async_process(check_sqs)
            PROCESSES.append(process1)
            PROCESSES += load_adaptors()
            PROCESSES += await load_pipelines()
            await update_available_blocks()
            for process in PROCESSES:
                process.join()
        except Exception as e:
            logger.error("An error %s", e)

