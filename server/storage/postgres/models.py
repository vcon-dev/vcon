from peewee import (
    Model,
    DateTimeField,
    CharField,
    IntegerField,
)
from playhouse.postgres_ext import PostgresqlDatabase, BinaryJSONField
from playhouse.db_url import parse
import os



db_params = parse(os.environ["MONOREPO_DATABASE_URL"])
db_name = db_params["database"]
del db_params["database"]
# Incompleted transactions with PostgreSQL:
# https://github.com/coleifer/peewee/issues/240#issuecomment-32126793
database = PostgresqlDatabase(db_name, autocommit=True, autorollback=True, **db_params)


class BaseModel(Model):
    class Meta:
        database = database
        legacy_table_names = False


class CallLogs(BaseModel):
    id = CharField(primary_key=True, index=True)
    agent_extension = CharField(null=True)
    agent_cxm_id = CharField(null=True)
    agent_cached_details = BinaryJSONField(null=True)
    dealer_number = CharField(null=True)
    dealer_cxm_id = CharField(null=True)
    dealer_cached_details = BinaryJSONField(null=True)
    customer_number = CharField(null=True)
    direction = CharField(null=True)
    disposition = CharField(null=True)
    s3_key = CharField(null=True)
    call_started_on = DateTimeField(null=True)
    duration = IntegerField(null=True)
    transcript = CharField(null=True)
    created_on = DateTimeField(null=True)
    modified_on = DateTimeField(null=True)
    json_version = CharField(null=True)
    cdr_json = BinaryJSONField(null=True)
    dialog_json = BinaryJSONField(null=True)
    source = CharField(null=True)

    class Meta:
        table_name = "call_logs"
