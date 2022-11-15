import os

MONGODB_URL=os.getenv("MONGO_URL", "mongodb://localhost:27017")
DEEPGRAM_KEY=os.environ["DEEPGRAM_KEY"]
AWS_KEY_ID=os.environ["AWS_KEY_ID"]
AWS_SECRET_KEY=os.environ["AWS_SECRET_KEY"]
AWS_BUCKET=os.environ["AWS_BUCKET"]
REDIS_URL=os.getenv("REDIS_URL", "redis://localhost")
LOG_LIMIT=os.getenv("LOG_LIMIT", 100)
HOSTNAME=os.getenv("HOSTNAME", "http://localhost:8000")