from peewee import *
from playhouse.reflection import generate_models, print_model, print_table_sql

import asyncio
import async_timeout
import redis.asyncio as redis
import json
import logging

logger = logging.getLogger(__name__)

async def start():
    database = PostgresqlDatabase('conserver_call_logs', user='conserver', password='gkcAFaf@hcBYQfb6', host='localhost', port=5432)
    models = generate_models(database)
    globals().update(models)
    logger.info("Starting the postgres storage adapter")

    while True:
        try:
            async with async_timeout.timeout(5):
                # Setup redis
                r = redis.Redis(host='localhost', port=6379, db=0)
                pubsub = r.pubsub()
                await pubsub.subscribe("storage-events")
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        body = json.loads(message['data'].decode())
                        logger.info("postgres received vCon: {}".format(body['uuid']))
                        for analysis in body['analysis']:
                            if (analysis['kind'] == 'projection'):
                                row = call_logs.create(**analysis['payload'])
                                row.create()

                        await asyncio.sleep(1)

        except asyncio.TimeoutError:
            pass

        except asyncio.CancelledError:
            print("postgres projection Cancelled")
            break

        except Exception as e:
            logger.debug("postgres projection error: {}".format(e))
