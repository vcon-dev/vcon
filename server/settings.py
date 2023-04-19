import os

MONGODB_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DEEPGRAM_KEY = os.getenv("DEEPGRAM_KEY")
AWS_KEY_ID = os.getenv("AWS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_BUCKET = os.getenv("AWS_BUCKET")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost")
LOG_LIMIT = os.getenv("LOG_LIMIT", 100)
TICK_INTERVAL = os.getenv("TICK_INTERVAL", 5)
HOSTNAME = os.getenv("HOSTNAME", "http://localhost:8000")
ENV = os.getenv("ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
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
EXTERNAL_WORKERS = os.getenv("EXTERNAL_WORKERS", False)