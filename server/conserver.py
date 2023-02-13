from fastapi.applications import FastAPI

# Load FastAPI app
app = FastAPI()
FastAPI.conserver_app = app

import api  # noqa
import lifecycle  # noqa
