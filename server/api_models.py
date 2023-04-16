from pydantic import BaseModel, Json
import typing
from datetime import datetime
from uuid import UUID
import enum

class Chain(BaseModel):
    links: typing.List[str] = []
    ingress_lists: typing.List[str] = []
    storage: typing.List[str] = []
    egress_lists: typing.List[str] = []
    enabled: int = 1

class Link(BaseModel):
    module: str
    options: typing.Dict[str, typing.Any] = {}
    ingress_lists: typing.List[str] = []
    egress_lists: typing.List[str] = []

class Storage(BaseModel):
    module: str
    options: typing.Dict[str, typing.Any] = {}


class Party(BaseModel):
    tel: str = None
    stir: str = None
    mailto: str = None
    name: str = None
    validation: str = None
    jcard: Json = None
    gmlpos: str = None
    civicaddress: str = None
    timezone: str = None


class DialogType(str, enum.Enum):
    recording = "recording"
    text = "text"


class Dialog(BaseModel):
    type: DialogType
    start: typing.Union[int, str, datetime]
    duration: float = None
    parties: typing.Union[int, typing.List[typing.Union[int, typing.List[int]]]]
    mimetype: str = None
    filename: str = None
    body: str = None
    url: str = None
    encoding: str = None
    alg: str = None
    signature: str = None


class Analysis(BaseModel):
    type: str
    dialog: int
    mimetype: str = None
    filename: str = None
    vendor: str = None
    _schema: str = None
    body: str = None
    encoding: str = None
    url: str = None
    alg: str = None
    signature: str = None


class Attachment(BaseModel):
    type: str
    party: int = None
    mimetype: str = None
    filename: str = None
    body: str = None
    encoding: str = None
    url: str = None
    alg: str = None
    signature: str = None


class Group(BaseModel):
    uuid: UUID
    body: Json = None
    encoding: str = None
    url: str = None
    alg: str = None
    signature: str = None


class Vcon(BaseModel):
    vcon: str
    uuid: UUID
    created_at: typing.Union[int, str, datetime] = datetime.now().timestamp()
    subject: str = None
    redacted: dict = None
    appended: dict = None
    group: typing.List[Group] = []
    parties: typing.List[Party] = []
    dialog: typing.List[Dialog] = []
    analysis: typing.List[Analysis] = []
    attachments: typing.List[Attachment] = []