import pytest
from vcon import Vcon
import json

"""
This covers testing the main methods of the Vcon class, including:

Building from JSON
Building a new instance
Adding and retrieving tags
Adding and finding attachments
Adding and finding analysis
Adding parties and dialogs
Serializing to JSON
Generating a UUID8 based on a domain name


"""
def test_build_from_json():
    json_string = '{"uuid": "12345", "vcon": "0.0.1", "created_at": "2023-05-02T12:00:00+00:00", "redacted": {}, "group": [], "parties": [], "dialog": [], "attachments": [], "analysis": []}'
    vcon = Vcon.build_from_json(json_string)
    assert vcon.uuid == "12345"
    assert vcon.vcon == "0.0.1"
    assert vcon.created_at == "2023-05-02T12:00:00+00:00"


def test_build_new():
    vcon = Vcon.build_new()
    assert vcon.uuid is not None
    assert vcon.vcon == "0.0.1"
    assert vcon.created_at is not None


def test_tags():
    vcon = Vcon.build_new()
    assert vcon.tags is None
    
    vcon.add_tag("test_tag", "test_value")
    assert vcon.get_tag("test_tag") == "test_value"


def test_add_attachment():
    vcon = Vcon.build_new()
    vcon.add_attachment(body={"key": "value"}, type="test_type")
    attachment = vcon.find_attachment_by_type("test_type")
    assert attachment["body"] == {"key": "value"}


def test_add_analysis():
    vcon = Vcon.build_new()
    vcon.add_analysis(type="test_type", dialog=[1, 2], vendor="test_vendor", body={"key": "value"})
    analysis = vcon.find_analysis_by_type("test_type")
    assert analysis["body"] == {"key": "value"}
    assert analysis["dialog"] == [1, 2]
    assert analysis["vendor"] == "test_vendor"


def test_add_party():
    vcon = Vcon.build_new()
    vcon.add_party({"id": "party1"})
    assert vcon.find_party_index("id", "party1") == 0


def test_add_dialog():
    vcon = Vcon.build_new()
    vcon.add_dialog({"id": "dialog1"})
    assert vcon.find_dialog("id", "dialog1") == {"id": "dialog1"}


def test_to_json():
    vcon = Vcon.build_new()
    json_string = vcon.to_json()
    assert json.loads(json_string) == vcon.to_dict()


def test_uuid8_domain_name():
    uuid8 = Vcon.uuid8_domain_name("test.com")
    assert uuid8[14] == "8"  # check version is 8


def test_get_tag():
    vcon = Vcon.build_new()
    vcon.add_tag("test_tag", "test_value")
    assert vcon.get_tag("test_tag") == "test_value"
    assert vcon.get_tag("nonexistent_tag") is None


def test_find_attachment_by_type():
    vcon = Vcon.build_new()
    vcon.add_attachment(body={"key": "value"}, type="test_type")
    assert vcon.find_attachment_by_type("test_type") == {"type": "test_type", "body": {"key": "value"}, "encoding": "json"}
    assert vcon.find_attachment_by_type("nonexistent_type") is None


def test_find_analysis_by_type():
    vcon = Vcon.build_new()
    vcon.add_analysis(type="test_type", dialog=[1, 2], vendor="test_vendor", body={"key": "value"})
    assert vcon.find_analysis_by_type("test_type") == {"type": "test_type", "dialog": [1, 2], "vendor": "test_vendor", "body": {"key": "value"}, "encoding": "json"}
    assert vcon.find_analysis_by_type("nonexistent_type") is None


def test_find_party_index():
    vcon = Vcon.build_new()
    vcon.add_party({"id": "party1"})
    assert vcon.find_party_index("id", "party1") == 0
    assert vcon.find_party_index("id", "nonexistent_party") is None


def test_find_dialog():
    vcon = Vcon.build_new()
    vcon.add_dialog({"id": "dialog1"})
    assert vcon.find_dialog("id", "dialog1") == {"id": "dialog1"}
    assert vcon.find_dialog("id", "nonexistent_dialog") is None


def test_properties():
    json_string = '{"uuid": "12345", "vcon": "0.0.1", "created_at": "2023-05-02T12:00:00+00:00", "redacted": {"key": "value"}, "group": [1, 2], "parties": [{"id": "party1"}], "dialog": [{"id": "dialog1"}], "attachments": [{"type": "test_type", "encoding":"none", "body": {"key": "value"}}], "analysis": [{"type": "test_type", "dialog": [1, 2], "vendor": "test_vendor", "body": {"key": "value"}}]}'
    vcon = Vcon.build_from_json(json_string)
    assert vcon.uuid == "12345"
    assert vcon.vcon == "0.0.1"
    assert vcon.created_at == "2023-05-02T12:00:00+00:00"
    assert vcon.redacted == {"key": "value"}
    assert vcon.group == [1, 2]
    assert vcon.parties == [{"id": "party1"}]
    assert vcon.dialog == [{"id": "dialog1"}]
    assert vcon.attachments == [{"type": "test_type", "encoding":"none", "body": {"key": "value"}}]
    assert vcon.analysis == [{"type": "test_type", "dialog": [1, 2], "vendor": "test_vendor", "body": {"key": "value"}}]


def test_to_dict():
    vcon = Vcon.build_new()
    vcon_dict = vcon.to_dict()
    assert isinstance(vcon_dict, dict)
    assert vcon_dict == json.loads(vcon.to_json())


def test_dumps():
    vcon = Vcon.build_new()
    json_string = vcon.dumps()
    assert isinstance(json_string, str)
    assert json_string == vcon.to_json()


def test_error_handling():
    with pytest.raises(json.JSONDecodeError):
        Vcon.build_from_json("invalid_json")
    