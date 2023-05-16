from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
from playhouse.postgres_ext import PostgresqlExtDatabase, ArrayField, JSONField
from peewee import (
    Model,
    DateTimeField,
    IntegerField,
    TextField,
    DecimalField,
    UUIDField,
    CompositeKey,
)

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

        class Party(BaseModel):
            tel = TextField(null = True)
            stir = TextField(null = True)
            mailto = TextField(null = True)
            name = TextField(null = True)
            validation = TextField(null = True)
            jcard = JSONField(null = True)
            gmlpos = TextField(null = True)
            civicaddress = TextField(null = True)
            timezone = TextField(null = True)
            vcon_uuid = UUIDField()
            index = IntegerField()

            class Meta:
                primary_key = CompositeKey("vcon_uuid", "index")

        class Dialog(BaseModel):
            type = TextField()
            start = DateTimeField(null = True)
            duration = DecimalField(null = True)
            parties = ArrayField(IntegerField)
            mimetype = TextField(null = True)
            filename = TextField(null = True)
            body = TextField(null = True)
            url = TextField(null = True)
            encoding = TextField(null = True)
            alg = TextField(null = True)
            signature = TextField(null = True)
            vcon_uuid = UUIDField()
            index = IntegerField()

            class Meta:
                primary_key = CompositeKey("vcon_uuid", "index")

        class Analysis(BaseModel):
            type = TextField()
            dialog = IntegerField()
            mimetype = TextField(null = True)
            filename = TextField(null = True)
            vendor = TextField()
            schema = TextField(null = True)
            body = TextField(null = True)
            encoding = TextField(null = True)
            url = TextField(null = True)
            alg = TextField(null = True)
            signature = TextField(null = True)
            vcon_uuid = UUIDField()
            index = IntegerField()

            class Meta:
                primary_key = CompositeKey("vcon_uuid", "index")

        class Attachment(BaseModel):
            type = TextField()
            party = IntegerField(null = True)
            mimetype = TextField(null = True)
            filename = TextField(null = True)
            body = TextField(null = True)
            encoding = TextField(null = True)
            url = TextField(null = True)
            alg = TextField(null = True)
            signature = TextField(null = True)
            vcon_uuid = UUIDField()
            index = IntegerField()

            class Meta:
                primary_key = CompositeKey("vcon_uuid", "index")

        class Group(BaseModel):
            uuid = UUIDField()
            body = JSONField(null = True)
            encoding = TextField(null = True)
            url = TextField(null = True)
            alg = TextField(null = True)
            signature = TextField(null = True)
            vcon_uuid = UUIDField()
            index = IntegerField()

            class Meta:
                primary_key = CompositeKey("vcon_uuid", "index")

        class Redacted(BaseModel):
            body = JSONField(null = True)
            encoding = TextField(null = True)
            url = TextField(null = True)
            alg = TextField(null = True)
            signature = TextField(null = True)
            vcon_uuid = UUIDField()

        class Vcons(BaseModel):
            id = UUIDField(primary_key=True)
            vcon = TextField()
            uuid = UUIDField()
            created_at = DateTimeField()
            updated_at = DateTimeField(null = True)
            subject = TextField(null = True)

        db.create_tables([Vcons, Dialog, Analysis, Attachment, Party, Group], safe=True)

        vcon_data = {
            "id": vcon.uuid,
            "uuid": vcon.uuid,
            "vcon": vcon.vcon,
            "created_at": vcon.created_at,
            "updated_at": vcon.created_at,
            "subject": vcon.subject,
        }
        Vcons.insert(**vcon_data).on_conflict(
            conflict_target=(Vcons.id), update=vcon_data
        ).execute()

        for ind, dialog in enumerate(vcon.dialog):
            Dialog.insert(vcon_uuid=vcon.uuid, index=ind, **dialog).on_conflict(
                conflict_target=(Dialog.vcon_uuid, Dialog.index), update=dialog
            ).execute()

        for ind, analysis in enumerate(vcon.analysis):
            Analysis.insert(vcon_uuid=vcon.uuid, index=ind, **analysis).on_conflict(
                conflict_target=(Analysis.vcon_uuid, Analysis.index), update=analysis
            ).execute()

        for ind, attachment in enumerate(vcon.attachments):
            Attachment.insert(vcon_uuid=vcon.uuid, index=ind, **attachment).on_conflict(
                conflict_target=(Attachment.vcon_uuid, Attachment.index),
                update=attachment,
            ).execute()

        for ind, party in enumerate(vcon.parties):
            Party.insert(vcon_uuid=vcon.uuid, index=ind, **party).on_conflict(
                conflict_target=(Party.vcon_uuid, Party.index), update=party
            ).execute()

        for ind, group in enumerate(vcon.group):
            Group.insert(vcon_uuid=vcon.uuid, index=ind, **group).on_conflict(
                conflict_target=(Group.vcon_uuid, Group.index), update=group
            ).execute()

        db.close() # close connection to database
        logger.info(f"postgres storage plugin: inserted vCon: {vcon_uuid}, results: {vcon} ")

    except Exception as e:
        logger.error(f"postgres storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ")
    finally:
        db.close() # close connection to database
