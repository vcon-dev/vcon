from lib.logging_utils import init_logger
from server.lib.vcon_redis import VconRedis
from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.postgres_ext import *

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

        class Group(BaseModel):
            uuid = UUIDField()
            body = JSONField(null = True)
            encoding = TextField(null = True)
            url = TextField(null = True)
            alg = TextField(null = True)
            signature = TextField(null = True)
            vcon_uuid = UUIDField()

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
 
        Vcons.create(
            id=vcon.uuid,
            uuid=vcon.uuid,
            vcon=vcon.vcon,
            created_at=vcon.created_at,
            updated_at=vcon.created_at,
            subject=vcon.subject,
            redacted=vcon.redacted,
            appended=vcon.appended,
        )
        for dialog in vcon.dialog:
            Dialog.create(vcon_uuid=vcon.uuid, **dialog)

        for analysis in vcon.analysis:
            Analysis.create(vcon_uuid=vcon.uuid, **analysis)
            
        for attachment in vcon.attachments:
            Attachment.create(vcon_uuid=vcon.uuid, **attachment)

        for party in vcon.parties:
            Party.create(vcon_uuid=vcon.uuid, **party)
            
        for group in vcon.group:
            Group.create(vcon_uuid=vcon.uuid, **group)
        
        db.close() # close connection to database
        logger.info(f"postgres storage plugin: inserted vCon: {vcon_uuid}, results: {vcon} ")

    except Exception as e:
        logger.error(f"postgres storage plugin: failed to insert vCon: {vcon_uuid}, error: {e} ")
    finally:
        db.close() # close connection to database
