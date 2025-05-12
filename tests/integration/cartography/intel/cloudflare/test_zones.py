from unittest.mock import patch

import requests

import cartography.intel.cloudflare.zones
import tests.data.cloudflare.zones
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(cartography.cloudflare.zones, 'get', return_value=tests.data.cloudflare.zones.CLOUDFLARE_CLOUDFLARES)
def test_load_cloudflare_zones(mock_api, neo4j_session):
    """
    Ensure that zones actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.cloudflare.com",
    }

    # Act
    cartography.intel.cloudflare.zones.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Zones exist
    expected_nodes = {
        # CHANGEME: Add here expected node from data
        # (123456, 'john.doe@domain.tld'),
    }
    assert check_nodes(
        neo4j_session,
        'CloudflareZone',
        ['id', 'email']
    ) == expected_nodes

