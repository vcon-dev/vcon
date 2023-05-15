FROM python:3.10.5

RUN apt-get update && \
    apt-get install -y libavdevice-dev ffmpeg

# Install SoX dependency
# https://pysox.readthedocs.io/en/latest/#installation
RUN apt-get install -y libsox-fmt-all sox
RUN pip install --upgrade pip

WORKDIR /app/server

ADD ./server/requirements.txt /app/server/requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

ADD  . /app

CMD [ "python", "./conserver.py" ]