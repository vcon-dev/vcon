import vcon_fixture
import vcon
import json
import pytest

_vcon = vcon_fixture.generate_mock_vcon()


def test_encoding():
    print("test_vcon:", _vcon)
    test_vcon = vcon.Vcon(_vcon)

    with pytest.raises(Exception):
        test_vcon.add_attachment(
            type="test_encoding",
            body={"key": "value"},
            encoding="json",
        )

    with pytest.raises(Exception):
        test_vcon.add_attachment(
                type= "test_encoding",
                body=["key", "value"],
                encoding= "base64url",
        )

    test_vcon.add_attachment(
            type= "test_encoding_str",
            body= "String value",
            encoding= "none",
    )
    assert test_vcon.find_attachment_by_type("test_encoding_str") == {
        "type": "test_encoding_str",
        "body": "String value",
        "encoding": "none",
    }

    test_vcon.add_attachment(
            type= "test_encoding_json",
            body= json.dumps({"key": "value"}),
            encoding= "json",
        
    )
    assert test_vcon.find_attachment_by_type("test_encoding_json") == {
        "type": "test_encoding_json",
        "body": json.dumps({"key": "value"}),
        "encoding": "json",
    }
