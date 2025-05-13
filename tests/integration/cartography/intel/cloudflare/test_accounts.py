from unittest.mock import patch

import requests

import cartography.intel.cloudflare.accounts
import tests.data.cloudflare.accounts
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.cloudflare.accounts,
    "get",
    return_value=tests.data.cloudflare.accounts.CLOUDFLARE_CLOUDFLARES,
)
def test_load_cloudflare_accounts(mock_api, neo4j_session):
    """
    Ensure that accounts actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.cloudflare.com",
    }

    # Act
    cartography.intel.cloudflare.accounts.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Accounts exist
    expected_nodes = {
        # CHANGEME: Add here expected node from data
        # (123456, 'john.doe@domain.tld'),
    }
    assert (
        check_nodes(neo4j_session, "CloudflareAccount", ["id", "email"])
        == expected_nodes
    )
