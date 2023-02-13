import asyncio
import redis.asyncio as redis
import asyncio
from lib.logging_utils import init_logger
from settings import REDIS_URL
from redis.commands.json.path import Path
import traceback
from .models import ShelbyUser, ShelbyLead
import datetime 


logger = init_logger(__name__)


default_options = {
    "name": "postgres",
    "ingress-topics": ['ingress-vcons'],
    "egress-topics":[],
}
options = {}

r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
p = r.pubsub(ignore_subscribe_messages=True)

tod = datetime.datetime.now()
d = datetime.timedelta(days = 2)
last_fetch = tod - d

async def run(vConUuid, opts=default_options):
    global last_fetch

    
    try:
        inbound_vcon = await r.json().get(f"vcon:{str(vConUuid)}", Path.root_path())

        # Fetch the leads from the CXM
        leads = ShelbyLead.select().where(ShelbyLead.created_on > last_fetch)
        tod = datetime.datetime.now()
        d = datetime.timedelta(minutes=2)
        last_fetch = tod - d

        for party in inbound_vcon['parties']:
            if party.get('role') == 'agent':
                extension = party['extension']
                user = ShelbyUser.select().where(ShelbyUser.extension == extension).get()
                logger.info(f"Found user {user}")
    except Exception:
        logger.error("stitcher plugin: error: \n%s", traceback.format_exc())


async def start(opts=default_options):
    logger.info("Starting the stitcher plugin!!!")
    while True:
        try:
            await p.subscribe(*opts['ingress-topics'])
            async for message in p.listen():
                vConUuid = message['data']
                logger.info("stitcher plugin: received vCon: %s", vConUuid)
                await run(vConUuid, opts)
                for topic in opts['egress-topics']:
                    await r.publish(topic, vConUuid)

        except asyncio.CancelledError:
            logger.debug("stitcher plugin Cancelled")
            break
        except Exception:
            logger.error("stitcher plugin: error: \n%s", traceback.format_exc())
    logger.info("stitcher plugin stopped")



