import pymongo
import redis.asyncio as redis
import json
import os
import paramiko


from lib.logging_utils import init_logger
from settings import MONGODB_URL
from datetime import datetime
from server.lib.vcon_redis import VconRedis
from lib.logging_utils import init_logger
vcon_redis = VconRedis()
logger = init_logger(__name__)


default_options = {
        "name": "sftp", 
        "url":   "sftp://localhost", 
        "port": 22,
        "username": "username",
        "password": "password",
        "path":  ".",
        "add_timestamp_to_filename": True,
        "filename": "vcon",
        "extension": "json",
        }

async def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Saving vCon to sftp storage")
    transport = paramiko.Transport((opts['url'], opts['port']))
    transport.connect(username=opts['username'], password=opts['password'])
    class SFTPClient(paramiko.SFTPClient):
        def __init__(self, *args, **kwargs):
            super(SFTPClient, self).__init__(*args, **kwargs)
        def putfo(self, fo, remotepath, callback=None, confirm=True):
            return self.putfo(fo, remotepath, callback, confirm)
    sftp = SFTPClient.from_transport(transport)
    # Upload the vCon to the SFTP site
    try:
        vcon = await vcon_redis.get_vcon(vcon_uuid)
        filename = opts['filename']
        if opts['add_timestamp_to_filename']:
            filename += f"_{datetime.now().isoformat()}"
        filename += f".{opts['extension']}"
        sftp.putfo(vcon.dumps(), os.path.join(opts['path'], filename))
        logger.info(f"sftp storage plugin: uploaded vCon: {vcon_uuid} to {opts['url']}")
    except Exception as e:
        logger.error(f"sftp storage plugin: failed to upload vCon: {vcon_uuid}, error: {e} ")
        raise e
    finally:
        sftp.close()
        transport.close()
        