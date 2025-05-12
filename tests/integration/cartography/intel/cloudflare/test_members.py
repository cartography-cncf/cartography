from unittest.mock import patch

import requests

import cartography.intel.cloudflare.members
import tests.data.cloudflare.members
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(cartography.cloudflare.members, 'get', return_value=tests.data.cloudflare.members.CLOUDFLARE_CLOUDFLARES)
def test_load_cloudflare_members(mock_api, neo4j_session):
    """
    Ensure that members actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.cloudflare.com",
    }
    account_id = 'CHANGEME'  # CHANGEME: Add here expected parent id node

    # Act
    cartography.intel.cloudflare.members.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        account_id,
    )

    # Assert Members exist
    expected_nodes = {
        # CHANGEME: Add here expected node from data
        # (123456, 'john.doe@domain.tld'),
    }
    assert check_nodes(
        neo4j_session,
        'CloudflareMember',
        ['id', 'email']
    ) == expected_nodes

    # Assert Members are connected with Account
    expected_rels = {
        ('CHANGE_ME', account_id),  # CHANGEME: Add here one of Members id
    }
    assert check_rels(
        neo4j_session,
        'CloudflareMember', 'id',
        'CloudflareAccount', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels
