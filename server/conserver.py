from fastapi.applications import FastAPI

# Load FastAPI app
conserver_app = FastAPI()
FastAPI.conserver_app = conserver_app

# Now load all the modules
import api  # noqa
import lifecycle  # noqa
import admin  # noqa
import main_loop  # noqa
import openapi_plugin

