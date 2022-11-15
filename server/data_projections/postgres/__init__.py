from peewee import *
from playhouse.reflection import generate_models, print_model, print_table_sql

import asyncio
import async_timeout
import redis.asyncio as redis
import json
import logging

logger = logging.getLogger(__name__)

default_options = {
    "name": "postgres",
    "ingress-topics": ["ingress-vcons"],
    "egress-topics":["egress-vcons-1"],
    "projected_table_name":'conserver_call_logs', 
    "user":"conserver", 
    "password":"gkcAFaf@hcBYQfb6", 
    "host":"localhost",
    "port":5432
}
options = {}

async def start(opts=default_options):
    logger.info("Starting the postgres data projection plugin")
    try:
        logger.info("Starting the postgres storage adapter")

        database = PostgresqlDatabase(opts.get('projected_table_name'), user=opts.get('user'), password=opts.get('password'), host=opts.get('host'), port=opts.get('port'))
        models = generate_models(database)
        globals().update(models)
        r = redis.Redis(host='localhost', port=6379, db=0)
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(*opts['ingress-topics'])



        while True:
            try:
                message = await p.get_message()
                if message:
                    logger.debug("mongo plugin: message: {}".format(message))
                    vConUuid = message['data'].decode('utf-8')
                    logger.info("mongo plugin: received vCon: {}".format(vConUuid))
                    body = await r.get("vcon:{}".format(str(vConUuid)))
                    vCon = json.loads(body)
                    for analysis in body['analysis']:
                        if (analysis['kind'] == 'projection'):
                            # A little confusing, the call_logs object is 
                            # put into scope with models=generate_models(database) 
                            # and globals().update(models)
                            row = call_logs.create(**analysis['payload'])
                            row.create()
                    for topic in opts['egress-topics']:
                        await r.publish(topic, vConUuid)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("postgres plugin: error: {}".format(e))

    except asyncio.CancelledError:
        logger.debug("postgres data projection plugin Cancelled")

    logger.info("postgres data projection plugin stopped")
