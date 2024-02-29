FROM python:3.12.2

RUN apt-get update && \
    apt-get install -y libavdevice-dev ffmpeg

# Install SoX dependency
# https://pysox.readthedocs.io/en/latest/#installation
RUN apt-get install -y libsox-fmt-all sox

# This is required in order to wait for Redis
RUN apt-get install -y redis-tools
RUN pip install --upgrade pip

WORKDIR /app

# TODO Update to use Poetry
ADD  pyproject.toml /app
ADD  poetry.lock /app
RUN pip install poetry==1.8.0
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-interaction --no-root
ADD  . /app

ENV PYTHONPATH "${PYTHONPATH}:/app/:/app/server/"

ENTRYPOINT ["/app/docker/wait_for_redis.sh"]

CMD [ "python", "./server/conserver.py" ]
