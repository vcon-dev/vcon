from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
from playhouse.postgres_ext import PostgresqlExtDatabase, BinaryJSONField
from peewee import (
    Model,
    DateTimeField,
    TextField,
    UUIDField,
)
import json

logger = init_logger(__name__)
default_options = {"name": "postgres"}


async def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the postgres storage")
    try:
        # cannot have redis clients in the global context as they get
        # created on an async event loop which may go away.
        vcon_redis = VconRedis()
        vcon = await vcon_redis.get_vcon(vcon_uuid)
        # Connect to Postgres
        db = PostgresqlExtDatabase(
            opts['database'], 
            user=opts['user'], 
            password=opts['password'], 
            host=opts['host'], 
            port=opts['port'])
        
        class BaseModel(Model):
            class Meta:
                database = db

        class Vcons(BaseModel):
            id = UUIDField(primary_key=True)
            vcon = TextField()
            uuid = UUIDField()
            created_at = DateTimeField()
            updated_at = DateTimeField(null=True)
            subject = TextField(null=True)
            vcon_json = BinaryJSONField(null=True)

        db.create_tables([Vcons], safe=True)

        vcon_data = {
            "id": vcon.uuid,
            "uuid": vcon.uuid,
            "vcon": vcon.vcon,
            "created_at": vcon.created_at,
            "updated_at": vcon.created_at,
            "subject": vcon.subject,
            "vcon_json": json.loads(vcon.dumps()),
        }
        Vcons.insert(**vcon_data).on_conflict(
            conflict_target=(Vcons.id), update=vcon_data
        ).execute()

        db.close()
        logger.info(f"postgres storage plugin: inserted vCon: {vcon_uuid}, results: {vcon} ")

    except Exception as e:
        logger.error(f"postgres storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ")
    finally:
        db.close()
