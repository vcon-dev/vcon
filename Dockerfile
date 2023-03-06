FROM python:3.10.5
ADD  . /app
WORKDIR /app/server

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir
RUN pip install stable-ts

CMD [ "python", "./conserver.py" ]
