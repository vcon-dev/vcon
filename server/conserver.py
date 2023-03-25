from fastapi.applications import FastAPI
import uvicorn

# Load FastAPI app
app = FastAPI()
FastAPI.conserver_app = app

import api  # noqa
import lifecycle  # noqa
import admin  # noqa
