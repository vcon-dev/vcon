from unittest.mock import patch

import pytest
from adapters.bria import get_dealer_data

from server import redis_mgr


GRAPHQL_DEALERS_RESPONSE = {
    "581": {
        "id": 581,
        "name": "Union City CDJR",
        "outboundPhoneNumber": "678-981-6233",
        "team": {"id": 9, "name": "Blue Team"},
    }
}


@pytest.mark.asyncio
async def test_it_should_return_the_dealer():
    redis_client = redis_mgr.get_client()
    await redis_client.delete("dealers-data")

    with patch(
        "adapters.bria.fetch_dealers_data_from_graphql"
    ) as mock_fetch_dealers_data_from_graphql:
        mock_fetch_dealers_data_from_graphql.return_value = GRAPHQL_DEALERS_RESPONSE

        dealer_data = await get_dealer_data("581")
        assert dealer_data == GRAPHQL_DEALERS_RESPONSE.get("581")
        assert mock_fetch_dealers_data_from_graphql.call_count == 1

        # Make sure next function call will not introduce new GraphQL API call
        dealer_data = await get_dealer_data("581")
        assert dealer_data == GRAPHQL_DEALERS_RESPONSE.get("581")
        assert mock_fetch_dealers_data_from_graphql.call_count == 1

        # Make sure it return None for unknown dealer id
        dealer_data = await get_dealer_data("apple")
        assert dealer_data is None
        assert mock_fetch_dealers_data_from_graphql.call_count == 1

    await redis_client.delete("dealers-data")
