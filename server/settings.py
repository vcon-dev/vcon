import os
from pathlib import Path

MONGODB_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DEEPGRAM_KEY = os.getenv("DEEPGRAM_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost")
TICK_INTERVAL = int(os.getenv("TICK_INTERVAL", 5))
HOSTNAME = os.getenv("HOSTNAME", "http://localhost:8000")
ENV = os.getenv("ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOGGING_CONFIG_FILE = os.getenv("LOGGING_CONFIG_FILE", Path(__file__).parent / 'logging.conf')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STITCHER_DATABASE_URL = os.getenv(
    "STITCHER_DATABASE_URL", "postgres://localhost:5432/stitcher"
)
SLACK_TOKEN = os.getenv(
    "SLACK_TOKEN", "xoxb-1234567890-1234567890-1234567890-1234567890"
)
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY", "sk-1234567890-1234567890-1234567890-1234567890"
)
VCON_STORAGE="postgresql://postgres:a7h96dG4vdUWtGLSpCNG@conserver.coeic8iojiit.us-east-1.rds.amazonaws.com:5432/postgres"
#VCON_STORAGE="postgres://localhost:5432/vcon"
INDEX_NAME = "vcon"
WEVIATE_HOST=os.getenv("WEVIATE_HOST", "localhost:8000")
WEVIATE_API_KEY=os.getenv('WEVIATE_API_KEY')


