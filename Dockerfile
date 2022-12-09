FROM python:3.10.5
ADD  . /app
WORKDIR /app/server
RUN pip install -r requirements.txt

CMD [ "python", "./conserver.py" ]
