from unittest.mock import patch

import requests

import cartography.intel.cloudflare.roles
import tests.data.cloudflare.roles
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(cartography.cloudflare.roles, 'get', return_value=tests.data.cloudflare.roles.CLOUDFLARE_CLOUDFLARES)
def test_load_cloudflare_roles(mock_api, neo4j_session):
    """
    Ensure that roles actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.cloudflare.com",
    }
    account_id = 'CHANGEME'  # CHANGEME: Add here expected parent id node

    # Act
    cartography.intel.cloudflare.roles.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        account_id,
    )

    # Assert Roles exist
    expected_nodes = {
        # CHANGEME: Add here expected node from data
        # (123456, 'john.doe@domain.tld'),
    }
    assert check_nodes(
        neo4j_session,
        'CloudflareRole',
        ['id', 'email']
    ) == expected_nodes

    # Assert Roles are connected with Account
    expected_rels = {
        ('CHANGE_ME', account_id),  # CHANGEME: Add here one of Roles id
    }
    assert check_rels(
        neo4j_session,
        'CloudflareRole', 'id',
        'CloudflareAccount', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels
