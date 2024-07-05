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
from datetime import datetime

logger = init_logger(__name__)
default_options = {"name": "postgres"}


def save(
    vcon_uuid,
    opts=default_options,
):
    logger.info("Starting the Postgres storage for vCon: %s", vcon_uuid)
    try:
        vcon_redis = VconRedis()
        vcon = vcon_redis.get_vcon(vcon_uuid)
        # Connect to Postgres
        db = PostgresqlExtDatabase(
            opts["database"],
            user=opts["user"],
            password=opts["password"],
            host=opts["host"],
            port=opts["port"],
        )

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
            type = TextField()

        db.create_tables([Vcons], safe=True)

        source = None
        for a in vcon.attachments:
            if a["type"] == "ingress_info":
                if a['encoding'] == 'json':
                    source = json.loads(a["body"])["source"]
                else: 
                    source = a["body"]["source"]

        vcon_data = {
            "id": vcon.uuid,
            "uuid": vcon.uuid,
            "vcon": vcon.vcon,
            "created_at": vcon.created_at,
            "updated_at": datetime.now(),
            "subject": vcon.subject,
            "vcon_json": vcon.to_dict(),
            "type": source,
        }
        Vcons.insert(**vcon_data).on_conflict(
            conflict_target=(Vcons.id), update=vcon_data
        ).execute()

        db.close()
        logger.info("Finished the Postgres storage for vCon: %s", vcon_uuid)
    except Exception as e:
        logger.error(
            f"postgres storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} "
        )
    finally:
        db.close()


def get(
    vcon_uuid,
    opts=default_options,
):
    # logger.info("Starting the Postgres storage get for vCon: %s", vcon_uuid)
    try:
        # Connect to Postgres
        db = PostgresqlExtDatabase(
            opts["database"],
            user=opts["user"],
            password=opts["password"],
            host=opts["host"],
            port=opts["port"],
        )

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
            type = TextField()

        try:
            vcon = Vcons.get(Vcons.id == vcon_uuid)
        except Vcons.DoesNotExist:
            vcon = None

        return vcon.vcon_json if vcon else None
    except Exception as e:
        logger.error(
            f"Postgres storage plugin: failed to get vCon: {vcon_uuid}, error: {e} "
        )
    finally:
        db.close()
