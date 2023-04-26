FROM python:3.10.5

RUN apt-get update && \
    apt-get install -y libavdevice-dev ffmpeg

# Install SoX dependency
# https://pysox.readthedocs.io/en/latest/#installation
RUN apt-get install -y libsox-fmt-all sox

ADD  . /app
WORKDIR /app/server



RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

CMD [ "python", "./conserver.py" ]
