FROM python:3.10.5

RUN apt-get update && \
    apt-get install -y libavdevice-dev ffmpeg

# Install SoX dependency
# https://pysox.readthedocs.io/en/latest/#installation
RUN apt-get install -y libsox-fmt-all sox

# This is required in order to wait for Redis
RUN apt-get install -y redis-tools
RUN pip install --upgrade pip

WORKDIR /app/server

ADD ./server/requirements.txt /app/server/requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

ADD  . /app

ENTRYPOINT ["/app/wait_for_redis.sh"]

CMD [ "python", "./conserver.py" ]