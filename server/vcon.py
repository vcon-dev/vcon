import json
from typing import Optional, Union
import hashlib
import time
import uuid6
from datetime import datetime
from pydash import get as _get


_LAST_V8_TIMESTAMP = None


class Vcon:
    def __init__(self, vcon_dict={}):
        # deep copy
        self.vcon_dict = json.loads(json.dumps(vcon_dict))
        # TODO fix when body is optional and not present
        for attachment in self.vcon_dict["attachments"]:
            # assume json if encoding is not present
            if attachment.get("encoding", None) in ["json", None]:
                body = json.loads(attachment["body"])
                attachment["body"] = body

    @classmethod
    def build_from_json(cls, json_string: str):
        return cls(json.loads(json_string))

    @classmethod
    def build_new(cls):
        vcon_dict = {
            "uuid": cls.uuid8_domain_name("strolid.com"),
            "vcon": "0.0.1",
            "created_at": datetime.utcnow().isoformat()[:-3] + "+00:00",
            "redacted": {},
            "group": [],
            "parties": [],
            "dialog": [],
            "attachments": [],
            "analysis": [],
        }
        return cls(vcon_dict)

    @property
    def tags(self):
        return self.find_attachment_by_type("tags")

    def get_tag(self, tag_name):
        tags_attachment = self.find_attachment_by_type("tags")
        if not tags_attachment:
            return None
        tag = next(
            (t for t in tags_attachment["body"] if t.startswith(f"{tag_name}:")), None
        )
        if not tag:
            return None
        tag_value = tag.split(":")[1]
        return tag_value

    def add_tag(self, tag_name, tag_value):
        tags_attachment = self.find_attachment_by_type("tags")
        if not tags_attachment:
            tags_attachment = {
                "type": "tags",
                "body": [],
                "encoding": "json",
            }
            self.vcon_dict["attachments"].append(tags_attachment)
        tags_attachment["body"].append(f"{tag_name}:{tag_value}")

    def find_attachment_by_type(self, type):
        return next(
            (a for a in self.vcon_dict["attachments"] if a["type"] == type), None
        )

    def add_attachment(self, body: Union[dict, list, str], type, encoding="json"):
        if isinstance(body, str) and encoding == "json":
            body = json.loads(body)

        attachment = {
            "type": type,
            "body": body,
            "encoding": encoding,
        }
        self.vcon_dict["attachments"].append(attachment)

    def find_analysis_by_type(self, type):
        return next((a for a in self.vcon_dict["analysis"] if a["type"] == type), None)

    def add_analysis(self, type: str, dialog: Union[list, int], vendor: str, body: Union[dict, list, str], encoding="json", extra={}):
        if isinstance(body, str) and encoding == "json":
            body = json.loads(body)
        analysis = {
            "type": type,
            "dialog": dialog,
            "vendor": vendor,
            "body": body,
            "encoding": encoding,
            **extra,
        }
        self.vcon_dict["analysis"].append(analysis)

    def add_party(self, party: dict):
        self.vcon_dict["parties"].append(party)

    def find_party_index(self, by: str, val: str) -> Optional[int]:
        return next(
            (
                ind
                for ind, party in enumerate(self.vcon_dict["parties"])
                if _get(party, by) == val
            ),
            None,
        )

    def find_dialog(self, by: str, val: str) -> Optional[dict]:
        return next(
            (dialog for dialog in self.dialog if _get(dialog, by) == val),
            None,
        )

    def add_dialog(self, dialog: dict):
        self.vcon_dict["dialog"].append(dialog)

    def to_json(self):
        tmp_vcon_dict = json.loads(json.dumps(self.vcon_dict))
        for attachment in tmp_vcon_dict["attachments"]:
            # assume json if encoding is not present
            if attachment.get("encoding", None) in ["json", None]:
                attachment["body"] = json.dumps(attachment["body"])
        return json.dumps(tmp_vcon_dict)

    def to_dict(self):
        return json.loads(self.to_json())  # convert from internal dict format to vcon format

    def dumps(self):
        return self.to_json()

    @property
    def parties(self):
        return self.vcon_dict["parties"]

    @property
    def dialog(self):
        return self.vcon_dict["dialog"]

    @property
    def attachments(self):
        return self.vcon_dict["attachments"]

    @property
    def analysis(self):
        return self.vcon_dict["analysis"]

    @property
    def uuid(self):
        return self.vcon_dict["uuid"]

    @staticmethod
    def uuid8_domain_name(domain_name: str) -> str:
        """
        Generate a version 8 (custom) UUID using the upper 62 bits of the SHA-1 hash
        for the given DNS domain name string for custom_c and generating
        custom_a and custom_b the same way as unix_ts_ms and rand_a respectively
        for UUID version 7 (per IETF I-D draft-peabody-dispatch-new-uuid-format-04).

        Parameters:
        domain_name: a DNS domain name string, should generally be a fully qualified host
            name.

        Returns:
        UUID version 8 string
        """

        sha1_hasher = hashlib.sha1()
        sha1_hasher.update(bytes(domain_name, "utf-8"))
        dn_sha1 = sha1_hasher.digest()

        hash_upper_64 = dn_sha1[0:8]
        int64 = int.from_bytes(hash_upper_64, byteorder="big")

        uuid8_domain = Vcon.uuid8_time(int64)

        return uuid8_domain

    @staticmethod
    def uuid8_time(custom_c_62_bits: int) -> str:
        """
        Generate a version 8 (custom) UUID using the given custom_c and generating
        custom_a and custom_b the same way as unix_ts_ms and rand_a respectively
        for UUID version 7 (per IETF I-D draft-peabody-dispatch-new-uuid-format-04).

        Parameters:
        custom_c_62_bits: the 62 bit value as an integer to be used for custom_b
            portion of UUID version 8.

        Returns:
        UUID version 8 string
        """
        # This is partially from uuid6.uuid7 implementation:
        global _LAST_V8_TIMESTAMP

        nanoseconds = time.time_ns()
        if _LAST_V8_TIMESTAMP is not None and nanoseconds <= _LAST_V8_TIMESTAMP:
            nanoseconds = _LAST_V8_TIMESTAMP + 1
        timestamp_ms, timestamp_ns = divmod(nanoseconds, 10**6)
        subsec = uuid6._subsec_encode(timestamp_ns)

        # This is not what is in the vCon I-D.  It says random bits
        # not bits from the time stamp.  May want to change this
        subsec_a = subsec >> 8
        uuid_int = (timestamp_ms & 0xFFFFFFFFFFFF) << 80
        uuid_int |= subsec_a << 64
        uuid_int |= custom_c_62_bits

        # We lie about the version and then correct it afterwards
        uuid_str = str(uuid6.UUID(int=uuid_int, version=7))
        assert uuid_str[14] == "7"
        uuid_str = uuid_str[:14] + "8" + uuid_str[15:]

        return uuid_str
