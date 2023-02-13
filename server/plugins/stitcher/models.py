import os

from peewee import BooleanField, CharField, DateTimeField, Model
from playhouse.db_url import parse
from playhouse.postgres_ext import BinaryJSONField, PostgresqlDatabase

db_params = parse(os.environ["STITCHER_DATABASE_URL"])
db_name = db_params["database"]
del db_params["database"]
database = PostgresqlDatabase(db_name, autocommit=True, autorollback=True, **db_params)


class BaseModel(Model):
    class Meta:
        database = database
        legacy_table_names = False


class ShelbyUser(BaseModel):
    id = CharField(primary_key=True, index=True)
    email = CharField(null=True)
    name = CharField(null=True)
    is_active = BooleanField(null=True)
    zoho_contact_id = CharField(null=True)
    extension = CharField(null=True)
    enable_bria_recording = BooleanField(null=True)

    class Meta:
        table_name = "shelby_user"


class ShelbyLead(BaseModel):
    id = CharField(primary_key=True, index=True)
    created_on = DateTimeField(null=True)
    modified_on = DateTimeField(null=True)
    details = BinaryJSONField(null=True)
    assigned_to = CharField(null=True)

    class Meta:
        table_name = "shelby_lead"
