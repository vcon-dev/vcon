import pytest
from lib.links.filters import is_included
import vcon


@pytest.mark.asyncio
async def test_is_included():
    _vcon = vcon.Vcon()
    _vcon.attachments.append(
        {
            "type": "tags",
            "body": '["category:12"]',
        }
    )

    assert is_included(None, _vcon)
    assert is_included({}, _vcon)
    assert is_included(
        {
            "only_if": {
                "section": "attachments",
                "type": "tags",
                "includes": "category:12",
            }
        },
        _vcon,
    )
    assert not is_included(
        {
            "only_if": {
                "section": "attachments",
                "type": "tags",
                "includes": "category:1",
            }
        },
        _vcon,
    )
    assert not is_included(
        {
            "only_if": {
                "section": "analysis",
                "type": "customer_frustration",
                "includes": "NEEDS REVIEW",
            }
        },
        _vcon,
    )

    _vcon = vcon.Vcon()
    _vcon.analysis.append(
        {
            "type": "customer_frustration",
            "body": "foo bar NEEDS REVIEW bar foo",
        }
    )
    assert is_included(
        {
            "only_if": {
                "section": "analysis",
                "type": "customer_frustration",
                "includes": "NEEDS REVIEW",
            }
        },
        _vcon,
    )
    assert not is_included(
        {
            "only_if": {
                "section": "analysis",
                "type": "customer_frustration_123",
                "includes": "NEEDS REVIEW",
            }
        },
        _vcon,
    )
